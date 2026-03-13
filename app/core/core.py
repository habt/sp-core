import os
import json
import time
import math
import asyncio
import logging
from collections import deque,  Counter
from app.components.gpu import Gpu
from app.components.network import Network
from app.core.comm import ServicePlannerComm
from app.library.data import Update
from app.library.settings import (
    NETS_KEY, SERVERS_KEY, CONNECTIONS_KEY,
    NET_PRED_ID_KEY, NET_PRED_KEY, NET_PRED_VAR_KEY,
    GPU_PRED_ID_KEY, GPU_PRED_KEY, GPU_PRED_VAR_KEY,
    DEFAULT_EWMA_ALPHA, DEFAULT_HISTORY_LENGTH,
    DEFAULT_SIGMA_LEVEL, DEFAULT_SWITCHING_THRESHOLD_MS
)

TOPOLOGY_FILE = os.getcwd() + os.getenv("TOPOLOGY_FILE")

KEEP_ALIVE_INTERVAL = int(os.getenv("KEEP_ALIVE_INTERVAL", 2))
CORE_UPDATE_INTERVAL = int(os.getenv("CORE_UPDATE_INTERVAL", 2))
HYSTERISIS_THRESHOLD = int(os.getenv("HYSTERISIS_THRESHOLD",1))
SIGMA_LEVEL = float(os.getenv("SIGMA_LEVEL", DEFAULT_SIGMA_LEVEL))
EWMA_ALPHA = float(os.getenv("EWMA_COEFFICIENT", DEFAULT_EWMA_ALPHA))
SWITCHING_THRESOLD = float(os.getenv("SWITCHING_THRESHOLD_MS", DEFAULT_SWITCHING_THRESHOLD_MS))

DEFAULT_SERVER = os.getenv("DEFAULT_SERVER", "jetson_4")

logging.basicConfig(level=logging.INFO)  #TODO: use the env settings instead of hardcoding the level here



class ServicePlannerCore():
    
    def __init__(self, comm: ServicePlannerComm, data_file: str=None):
        self.stop_event = asyncio.Event()
        self.enabled = True
        self.comm = comm
        self.periodic_update_task = None
        self.update_send_time = None
        
        self.best_connection = None
        self.best_server = None
        self.candidate_server = None  # used by the hyterisis counter method of selection
        self.default_server = DEFAULT_SERVER
        
        self.keep_alive_interval = KEEP_ALIVE_INTERVAL
        self.update_interval = CORE_UPDATE_INTERVAL
        self.hysterisis_threshold = HYSTERISIS_THRESHOLD
        self.sigma_level = SIGMA_LEVEL
        self.ewma_alpha = EWMA_ALPHA
        self.switching_threshold = SWITCHING_THRESOLD
        self.hysterisis_counter = 0

        self.delay_history = deque(maxlen=DEFAULT_HISTORY_LENGTH)
        self.selection_history = deque(maxlen=DEFAULT_HISTORY_LENGTH)

        self.topology_file = TOPOLOGY_FILE
        self.servers = {}
        self.links = {}
        self.connections = {}
        self.init_components(data_file)


    def set_status(self, command):
        if command == "enable":
            self.enabled = True
        elif command == "disable":
            self.enabled = False
        else:
            logging.error(f"Unknown commad: {command}. Core enabled = {self.enabled}")
            return False
        return True

    
    def set_refresh_interval(self, interval: float):
        self.update_interval = interval
        logging.info(f"Refresh interval set to {self.update_interval} seconds")
    

    def set_hysterisis_threshold(self, window: float):
        if window is not None:
            self.hysterisis_threshold = window / self.update_interval
            logging.info(f"Hysterisis threshold set to {self.hysterisis_threshold}")
    

    def set_ewma_coefficient(self, coef: float):
        if coef is not None:
            self.ewma_alpha = coef
            logging.info(f"EWMA alpha set to {self.ewma_alpha}")
    

    def set_sigma_level(self, level: float):
        if level is not None:
            self.sigma_level = level
            
            for server in self.servers.values():
                server.set_sigma_level(level)
            
            for link in self.links.values():
                link.set_sigma_level(level)
            
            logging.info(f"Sigma level set to {self.sigma_level}")


    def set_parameters(self, control_params):
        try:
            self.set_refresh_interval(
                control_params['update'])
            self.set_hysterisis_threshold(
                control_params['hysteresis'])
            self.set_sigma_level(
                control_params['sigma'])
            self.set_ewma_coefficient(
                control_params['ewma'])
            return True
        except Exception as e:
            logging.error(f"Error in updating parameters. {e}")
            raise

    
    @staticmethod
    def create_component(comp_meta):
        print(f"Creating component from metadata: {comp_meta}")
        
        if comp_meta['type'] == 'gpu':
            return Gpu(comp_meta)
        elif comp_meta['type'] == 'network':
            return Network(comp_meta)
        else:
            raise ValueError("Unknown component type")


    def init_servers(self, servers_meta):
        logging.info("Loading GPU servers...")
        for server_id in servers_meta:
            self.servers[server_id] = self.create_component(servers_meta[server_id])


    def init_links(self, links_meta):
        logging.info("Loading network links...")
        for link_id in links_meta:
            self.links[link_id] = self.create_component(links_meta[link_id])


    def init_connections(self, conns_meta):
        logging.info("Loading network connections...")
        for conn_id in conns_meta:
            self.connections[conn_id] = {}
            self.connections[conn_id]['id'] = conns_meta[conn_id]['id']
            self.connections[conn_id]['path'] = conns_meta[conn_id]['path']


    def init_components(self, topo_file=None):
        topo_file = self.topology_file if topo_file is None else topo_file
        
        print(f"Loading path data from {topo_file}")
        with open(topo_file, "r") as f:
            data = json.load(f)
        
        self.init_links(data.get(NETS_KEY))  
        self.init_servers(data.get(SERVERS_KEY))
        self.init_connections(data.get(CONNECTIONS_KEY))


    def update_gpu_predictions(self):
        logging.info("Updating gpu predictions...")
        
        gpu_predictions = self.comm.request_gpu_update()
        
        if gpu_predictions is not None:                                                         # update the gpu predictions of each server/gpu if gpu predictions are available
            
            preds = gpu_predictions.get("predictions", [])
            #logging.info("Setting gpu predictions of servers: %s", preds)
            
            for pred in preds:
                server = next((self.servers[id] for id in self.servers if  id == pred['node_id']), None)

                #logging.info("Found server for gpu prediction: %s", server.address if server else "None")
                if server:
                    
                    server.set_prediction(
                        pred[GPU_PRED_KEY], 
                        pred[GPU_PRED_VAR_KEY]
                        )
            #logging.info("GPU predictions updated: %s", gpu_predictions)
        else:                                                                               # set the gpu predictions of each server/gpu to nan if gpu predictions do not exist
            logging.warning("No GPU predictions found. Setting predictions to nan")
            for server in self.servers.values():
                server.set_prediction(float('nan'), float('nan'))



    def update_net_predictions(self):
        logging.info("Updating network predictions...")

        net_predictions = self.comm.request_net_update()
        
        if net_predictions is not None:                                                     #  update the network predictions of each link if network predictions are available
            preds = net_predictions.get("servers", {}).values()
            #logging.info("Setting network predictions: %s", preds)
            
            for pred in preds: 
                link = next((self.links[id] for id in self.links if id == pred['server_id']), None)
                
                #logging.info("Found link for net prediction: %s", link.id if link else "None")
                if link:
                    
                    link.set_prediction(
                        pred[NET_PRED_KEY], 
                        pred[NET_PRED_VAR_KEY]
                        )
            #logging.info("Network predictions updated: %s", net_predictions)
        else:                                                                                    # set the network predictions of each link to nan if network predictions do not exist
            logging.warning("No network predictions found. Setting predictions to nan")
            for link in self.links.values():
                link.set_prediction(float('nan'), float('nan'))


    def calculate_connection_delay(self, connection) -> dict:
        tot = 0
        
        for comp_id in connection:
            if comp_id in self.servers:
                comp = self.servers[comp_id]
                server_id = comp_id
            elif comp_id in self.links:
                comp = self.links[comp_id]
            else:                
                print(f"Component {comp_id} not found in servers or links")
                continue
            
            if comp:
                tot += comp.get_curr_delay()

        return {"id": server_id, "delay": tot}


    def select_best_server_with_hysterisis_counter(self) -> None:   
        # Select the server with the lowest end-to-end delay
        shortest_conn_server_id = min(
            self.connections.values(),
            key=lambda x: x['e2e_delay']
        )['server_id']
        
        fastest_server = self.servers[shortest_conn_server_id]
        
        if fastest_server != self.best_server:
            logging.info("New fastest server: %s", fastest_server.get_id())
            if self.hysterisis_counter == 0:
                self.candidate_server = fastest_server
                logging.info(f"New candidate server {fastest_server.get_id()} selected, starting hysterisis counter")

            self.hysterisis_counter += 1
            
            logging.info(f"Hysterisis counter: {self.hysterisis_counter}")
            if fastest_server == self.candidate_server:
                logging.info(f"Fastest server {fastest_server.get_id()} = candidate server {self.candidate_server.get_id()}")
                if self.hysterisis_counter >= HYSTERISIS_THRESHOLD:
                    logging.info("Hysterisis threshold met, updating best server")
                    self.best_server = self.candidate_server
                    self.hysterisis_counter = 0
            else:
                self.candidate_server = fastest_server
                self.hysterisis_counter = 0
        else:
            self.candidate_server = fastest_server
            self.hysterisis_counter = 0

        #self.best_server = self.servers[shortest_conn_server_id]
        logging.info(f"Current fastest server: {shortest_conn_server_id}")
        print(f"Best server: {self.best_server.get_id() if self.best_server else 'None'}")
    

    def select_best_server_with_selection_history(self) -> None:
        shortest_conn_server_id = min(
            self.connections.values(),
            key=lambda x: x['e2e_delay']
        )['server_id']

        self.selection_history.append(shortest_conn_server_id)

        # Maintain a count of selections (server ids)
        counts = Counter(self.selection_history)
        most_common = counts.most_common(1)
        
        if most_common:
            logging.info(f"Most frequent server: {most_common[0][0]}")
            self.best_server = self.servers[most_common[0][0]]
        else:
            logging.error("Unable determine most frequent server")
            self.best_server = None


    def update_ewma_delay_of_connections(self):
        # Update EWMA delay for each connection
        for conn_id, conn in self.connections.items():
            e2e = conn.get('e2e_delay')
            if e2e is None:
                logging.warning(f"No e2e_delay for connection {conn_id}, skipping EWMA update")
                continue

            prev = conn.get('ewma_delay')

            # if previous EWMA is missing or NaN, initialize with current e2e_delay
            if prev is None or (isinstance(prev, float) and math.isnan(prev)):
                conn['ewma_delay'] = e2e
            else:
                conn['ewma_delay'] = (
                    (1 - self.ewma_alpha) * prev +
                    self.ewma_alpha * e2e
                )
            logging.info(f"{conn.get('path')}: current delay={conn.get('e2e_delay')}, ewma delay={conn.get('ewma_delay')}")



    def select_best_server_with_ewma(self) -> None:  
        self.update_ewma_delay_of_connections()
        
        # filter connections that actually have a numeric ewma_delay
        valid_conns = [c for c in self.connections.values()
                    if 'ewma_delay' in c and not math.isnan(c['ewma_delay']) and c['ewma_delay'] is not None]
        
        if not valid_conns:
            logging.error("No valid EWMA delays available to select fastest connection")
            self.best_server = self.servers.get(self.default_server)
            return

        candidate_conn = min(valid_conns, key=lambda x: x['ewma_delay'])

        if self.best_connection is not None:
            current_best_conn = None
            
            for conn in self.connections.values():
                if conn.get('id') == self.best_connection.get('id'):
                    current_best_conn = conn
                    break
            
            if candidate_conn.get('id') != current_best_conn.get('id'):
                improvement = current_best_conn.get('ewma_delay') - candidate_conn.get('ewma_delay')
                logging.info(f"Improvement by candidate {candidate_conn.get('server_id')}: {improvement}, Threshold: {self.switching_threshold}")
                
                if improvement > self.switching_threshold:
                    
                    self.best_connection = candidate_conn
                    new_best_conn_server_id = candidate_conn.get('server_id')
                    
                    if new_best_conn_server_id is None:
                        logging.error("Fastest connection missing server_id")
                        return

                    self.best_server = self.servers.get(new_best_conn_server_id)
                    logging.info(
                        "Switching threshold met. Changing from %s to %s",
                        current_best_conn.get('server_id'),
                        self.best_connection.get('server_id')
                        )
                else:
                    logging.info("Switching threshold NOT met." 
                                 "Continuing with current server."
                                 )
            else:
                logging.info("Candidate connection same as current connection."
                             "Continuing with current server."
                             )  
        else:
            self.best_connection = candidate_conn
            new_best_conn_server_id = candidate_conn['server_id']

            self.best_server = self.servers.get(new_best_conn_server_id)
        
        logging.info(
            "Current fastest server: %s, EWMA delay: %s",
            self.best_server.get_id(),
            self.best_connection['ewma_delay']
            )


    def update_best_server(self) -> None:
        logging.info("Selecting best server...")
        
        # Calculate end-to-end delays for all connections
        for conn in self.connections:
            delay = self.calculate_connection_delay(self.connections[conn]['path'])

            self.connections[conn]['e2e_delay'] = delay['delay']
            self.connections[conn]['server_id'] = delay['id']

        #self.update_best_server_with_hysterisis_counter()
        self.select_best_server_with_ewma()


    def update_server_selection(self):
        previous_server = self.best_server
        if self.enabled:
            logging.info("Updating predictions...")

            self.update_gpu_predictions()
            self.update_net_predictions()
            
            self.update_best_server()
        else:
            logging.info(f"Using default server {self.default_server}")
            self.best_server = self.servers[self.default_server]
        
        if self.update_send_time is not None:
            time_since_update = time.time() - self.update_send_time
        else:
            time_since_update = 0

        if previous_server != self.best_server or time_since_update > self.keep_alive_interval:
                asyncio.create_task(
                    self.comm.send_recommendation(
                        Update.UNSOLICITED.value, self.best_server.get_address() if self.best_server else None
                    )
                )
                logging.info(
                    "Best server update sent: %s, Update interval: %s",
                    self.best_server.get_id(),
                    time_since_update
                    )
                self.update_send_time = time.time()

    async def periodic_update(self):
        logging.info("Starting periodic update")
        try:
            while not self.stop_event.is_set():
                start = time.perf_counter()

                self.update_server_selection()
                elapsed = time.perf_counter() - start

                sleep_time = max(0, self.update_interval - elapsed)
                await asyncio.sleep(sleep_time)
                print(f"Periodic update completed in {elapsed:.2f} seconds, sleeping for {sleep_time:.2f} seconds")
        
        except asyncio.CancelledError:
            logging.error("Background task cancelled")
            raise
    

    async def start_periodic_update(self):
        self.stop_event.clear()
        
        try:
            if self.periodic_update_task is None or self.periodic_update_task.done():
                self.periodic_update_task = asyncio.create_task(self.periodic_update())
                logging.info("Periodic update task started")
            else:
                logging.warning("Periodic update task is already running")
        except Exception as e:
            logging.error(f"Error starting periodic update task: {e}")


    async def stop_periodic_update(self):
        self.stop_event.set()
        
        if self.periodic_update_task:
            try:
                self.periodic_update_task.cancel()
                await self.periodic_update_task
            
            except asyncio.CancelledError:
                logging.info("Periodic update task cancelled error")

        logging.info("Background task stopped cleanly")

    
    async def handle_recommendation_requests(self):
        logging.info("Recommendation request listener started")

        count = 0
        while True:
            logging.info(f"Waiting for recommendation request from SP agent: {count}")
            request = await self.comm.receive_recommendation_request()
            
            self.update_predictions()
            await self.comm.send_recommendation(
                Update.REQUESTED.value, self.best_server.get_address() if self.best_server else None
                )
            count +=1


if __name__ == "__main__":
    TOPOLOGY_FILE = "/home/habtes/sp_core/app/config/paths.json"
    sp_comm = ServicePlannerComm()
    sp_core = ServicePlannerCore(sp_comm, TOPOLOGY_FILE)
    logging.info(f"Loaded connections: {sp_core.connections}")