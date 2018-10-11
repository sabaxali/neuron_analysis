import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pymaid
import json

with open('/Users/alis10/Documents/pycharmprojects/catmaid_login.json') as login_file:
    catmaid_login = json.load(login_file)

token = catmaid_login['token']
username = catmaid_login['username']
password = catmaid_login['password']
rm = pymaid.CatmaidInstance('https://neuropil.janelia.org/tracing/fafb/v14', username, password, token)


class CatmaidApiTokenAuth(HTTPBasicAuth):
    """Attaches HTTP X-Authorization Token headers to the given Request.
    Optionally, Basic HTTP Authentication can be used in parallel.
    """

    def __init__(self, token, username=None, password=None):
        super(CatmaidApiTokenAuth, self).__init__(username, password)
        self.token = token

    def __call__(self, r):
        r.headers['X-Authorization'] = 'Token {}'.format(self.token)
        if self.username and self.password:
            super(CatmaidApiTokenAuth, self).__call__(r)
        return r


class NeuronConnectivity:

    """pass in single id (int), can not pass in list because pymaid only allows
    distance matrix for once skeleton at a time"""

    def __init__(self, skeleton_id):
        self.skeleton_id = skeleton_id
        self.source_neuron = pymaid.get_neuron(skeleton_id)
        self.despiked_neuron = pymaid.despike_neuron(self.source_neuron, sigma=5, inplace=False)
        self.neuron_type_dict = {
            'PBG5': {'P-EN1': {'neuron_id': [649823, 668576], 'glom_color': 'salmon', 'default_color': 'red'},
                     'P-EN2': {'neuron_id': [806288, 2703303], 'glom_color': 'salmon', 'default_color': 'pink'},
                     'P-EG': {'neuron_id': [1032767, 3849973], 'glom_color': 'salmon', 'default_color': 'deepskyblue'},
                     'E-PG': {'neuron_id': [4087066, 3457743, 1568214, 861090,
                                            4210786, 437814], 'glom_color': 'salmon', 'default_color': 'darkmagenta'}},
            'PBG6': {'P-EN1': {'neuron_id': [525851, 607812, 3338987, 3423772], 'glom_color': 'aqua',
                               'default_color': 'red'},
                     'P-EN2': {'neuron_id': [659759, 3286828, 3349747, 3491680], 'glom_color': 'aqua',
                               'default_color': 'pink'},
                     'P-EG': {'neuron_id': [963438, 3512247], 'glom_color': 'aqua', 'default_color': 'deepskyblue'},
                     'E-PG': {'neuron_id': [1274268, 1274114, 4040702, 676911, 1274528], 'glom_color': 'aqua',
                              'default_color': 'darkmagenta'}},
            'PBG7': {'P-EN1': {'neuron_id': [827466, 828911], 'glom_color': 'violet', 'default_color': 'red'},
                     'P-EN2': {'neuron_id': [1625086, 1639675], 'glom_color': 'violet', 'default_color': 'pink'}},
            'No_PB': {'G-E': {'neuron_id': [432766], 'default_color': 'gold'},
                      'Bidirectional Ring': {'neuron_id': [6346245, 6353358, 6417166, 6813859, 7014054,
                                             7014310, 7029666, 6393609], 'default_color': 'orange'}}}

    def filter_skid_data(self, pre_or_post, min_num_nodes=1):

        """Select if upstream(post) or downstream(pre) synaptic partners are wanted
         and can also filter by number of nodes on partner skeleton"""

        self.filtered_partner_nodes_list = []
        for item in self.skeleton_id:
            req = requests.post('https://neuropil.janelia.org/tracing/fafb/v14/1/skeletons/connectivity',
                              data={'source_skeleton_ids[]': [item], 'boolean_op': 'OR', 'with_nodes': 'true'},
                              auth=CatmaidApiTokenAuth(token, username, password))
            source_neuron_data = req.json()
            if pre_or_post == 'pre':
                synapse_direction = source_neuron_data['outgoing']
                self.columntitle = 'post_neuron'
            if pre_or_post == 'post':
                synapse_direction = source_neuron_data['incoming']
                self.columntitle = 'pre_neuron'
            for neuron in synapse_direction:
                num_nodes = synapse_direction[neuron]['num_nodes']
                if num_nodes >= min_num_nodes:
                    filtered_partner_nodes_dict = {neuron: synapse_direction[neuron]}
                    self.filtered_partner_nodes_list.append(filtered_partner_nodes_dict)

    def get_df(self):

        """Returns a connectivity table with distance values of synaptic sites """

        self.connectivity_df = []
        value_list = []
        source_root = self.source_neuron.root[0]
        distance_matrix = pymaid.geodesic_matrix(x=self.despiked_neuron, tn_ids=[source_root])
        for partner_dict in self.filtered_partner_nodes_list:
            T1_list = []
            partner_id = list(partner_dict.keys())[0]
            source_id = ((list(partner_dict[partner_id]['skids'].keys()))[0])
            partner_id_name = pymaid.get_names(partner_id)[partner_id]
            self.source_id_name = (pymaid.get_names(source_id)[source_id])
            correct_synapse_count = (partner_dict[partner_id]['skids'][source_id][-1])
            for treenode_list in partner_dict[partner_id]['links']:
                        T1 = treenode_list[0] #treenode on source skeleton at synaptic site
                        T1_list.append(T1)
            synapse_count = len(T1_list)
            if synapse_count != correct_synapse_count:
                print('Number of treenode ids do not match number of synapses')
            distance_list = []
            node_distance_list = []
            for node in distance_matrix:
                for T1_node in T1_list:
                    if T1_node == node:
                        distance = distance_matrix.loc[source_root, node]
                        distance_list.append(distance)
                        node_distance_list.append({T1_node: distance})
            value = (partner_id, partner_id_name, synapse_count, self.source_id_name, source_id, T1_list,
                                 distance_list, node_distance_list)
            value_list.append(value)
        self.connectivity_df = pd.DataFrame(value_list,
                                            columns=['partner_id', self.columntitle, 'synapse_count', 'source_neuron',
                                                     'source_id', 'T1_nodes', 'distance', 'node_distance'])
        #print(self.connectivity_df)
        total_synapsecount = (np.sum(self.connectivity_df['synapse_count'].values))
        self.n_bins = int(np.sqrt(total_synapsecount))
        pd.set_option('display.max_rows', 500)
        pd.set_option('display.max_columns', 500)
        pd.set_option('display.width', 1000)


    def plot_hist(self, neuron_type=None, neuron_type2=None, PB_glom=None, PB_glom2=None, ring=False):
        """Purpose of identified neuron list is to be able to create ring list based on skeleton ids
        that are not in identified neuron list"""
        identified_neuron_list = []
        for column_key in self.neuron_type_dict:
            for neuron_key in self.neuron_type_dict[column_key]:
                for neuron_skids in (self.neuron_type_dict[column_key][neuron_key]['neuron_id']):
                    identified_neuron_list.append(str(neuron_skids))
        ring_neuron_list = []
        other_connections = self.connectivity_df[~self.connectivity_df['partner_id'].isin(identified_neuron_list)]
        for distance in other_connections['distance']:
            for values in distance:
                ring_neuron_list.append(values)

        if ring == True:
            plt.hist(ring_neuron_list, range=(15000, 90000), bins=self.n_bins, alpha=0.5, color='green', label='"Ring"')


        if PB_glom == None:
            neuron_distance_list = self.plot_type(neuron_type)
            neuron2_distance_list = self.plot_type(neuron_type2)
            hist_color = self.get_type_color(neuron_type)
            hist_color2 = self.get_type_color(neuron_type2)
            plt.hist(neuron_distance_list, range=(15000, 90000), bins=self.n_bins, alpha=0.5, color=hist_color,
                     label=neuron_type)
            plt.hist(neuron2_distance_list, range=(15000, 90000), bins=self.n_bins, alpha=0.5, color=hist_color2,
                     label=neuron_type2)

        if PB_glom != None:
            glom_distance_list = self.plot_glom(PB_glom, neuron_type)
            glom_color = self.get_glom_color(PB_glom)
            plt.hist(glom_distance_list, range=(15000, 90000), bins=self.n_bins, alpha=0.5, color=glom_color,
                     label=PB_glom + neuron_type)

        if PB_glom2 != None:
            glom2_distance_list = self.plot_glom(PB_glom2, neuron_type)
            glom2_color = self.get_glom_color(PB_glom2)
            plt.hist(glom2_distance_list, range=(15000, 90000), bins=self.n_bins, alpha=0.5, color=glom2_color,
                     label=PB_glom2 + neuron_type)

        plt.legend()
        plt.title(self.source_id_name)
        plt.ylabel('Number of synapses')
        plt.xlabel('Distance from root (nm)')
        # plt.show()

    def plot_type(self, neuron_type):
        distance_list = []
        for column_key in self.neuron_type_dict:
            self.get_distance(neuron_type, column_key, distance_list)
        return distance_list

    def plot_glom(self, PB_glom, neuron_type):
        distance_list = []
        for column_key in self.neuron_type_dict:
            if PB_glom == column_key:
                self.get_distance(neuron_type, column_key, distance_list)
        return (distance_list)

    def get_distance(self, neuron_type, column_key, distance_list):
        for neuron_key in self.neuron_type_dict[column_key]:
            if neuron_type == neuron_key:
                for neuron_id in self.neuron_type_dict[column_key][neuron_key]['neuron_id']:
                    neuron_df = self.connectivity_df.loc[self.connectivity_df['partner_id'] == str(neuron_id)]
                    for distance in neuron_df['distance']:
                        for values in distance:
                            distance_list.append(values)

    def get_type_color(self, neuron_type):
        for column_key in self.neuron_type_dict:
            for neuron_key in self.neuron_type_dict[column_key]:
                if neuron_type == neuron_key:
                    return self.neuron_type_dict[column_key][neuron_key]['default_color']

    def get_glom_color(self, PB_glom):
        for column_key in self.neuron_type_dict:
            if PB_glom == column_key:
                for neuron_key in self.neuron_type_dict[column_key]:
                    return self.neuron_type_dict[column_key][neuron_key]['glom_color']

