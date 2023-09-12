"""Example of using two different training methods at once in multi-agent.

Here we create a number of CartPole agents, some of which are trained with
DQN, and some of which are trained with PPO. We periodically sync weights
between the two algorithms (note that no such syncing is needed when using just
a single training method).

For a simpler example, see also: multiagent_cartpole.py
"""
# TODO (Kourosh): Migrate this example to the RLModule API.
import argparse

import gymnasium as gym
import os
from time import sleep
import ray
from ray.rllib.policy.policy import PolicySpec
from ray.rllib.algorithms.ppo import (
    PPOConfig,
    PPOTF1Policy,
    PPOTF2Policy,
    PPOTorchPolicy,
)
from ray.rllib.examples.env.multi_agent import MultiAgentCartPole
from ray.tune.logger import pretty_print
from ray.tune.registry import register_env

#new import
from gymnasium import spaces
import numpy as np
from ray.rllib.env.multi_agent_env import MultiAgentEnv


from pygame.locals import QUIT

import random
import pygame

'''
Le but du programme consiste à apprendre au superviseur et au 3 traitants
à se déplacer dans la grille en respectant les règles suivantes :
- Le superviseur affecte une sous-zone à chacun des 3 traitants ;
- Pour chaque sous-zone qui lui est affecté, le traitant visite chacune des croix contenues dans la sous-zone ;
- Une fois que les traitants ont fini de visiter les croix de leur sous-zones, le superviseur doit se rendre au
centre de chaque sous-zone ;
- Après sêtre rendu au centre des sous-zones traitées par les 3 traitants, le superviseur affecte une nouvelle
sous-zone à chacun des 3 traitants, le tout en progressant de gauche à droite afin que toutes les croix de la
grille soient visitées.
'''


class MobileSupervisor:
    def __init__(self):
        # Initialisation de la classe MobileSupervisor
        self._supervisor_x = None
        self._supervisor_y = None

    def get_x_pos(self):
        return self._supervisor_x

    def get_y_pos(self):
        return self._supervisor_y

    def set_x_pos(self, nouvelle_valeur):
        self._supervisor_x = nouvelle_valeur

    def set_y_pos(self, nouvelle_valeur):
        self._supervisor_y = nouvelle_valeur

    def moveTo(self):
        # Méthode de la classe MobileSupervisor
        pass

    def doThis(self):
        # Méthode de la classe MobileSupervisor
        pass

    def doThat(self):
        # Méthode de la classe MobileSupervisor
        pass

class MobileOperator:
    def __init__(self):
        # Initialisation de la classe MobileOperator
        self._supervisor_x = None
        self._supervisor_y = None

    def get_x_pos(self):
        return self._supervisor_x

    def get_y_pos(self):
        return self._supervisor_y

    def set_x_pos(self, nouvelle_valeur):
        self._supervisor_x = nouvelle_valeur

    def set_y_pos(self, nouvelle_valeur):
        self._supervisor_y = nouvelle_valeur

    def moveTo(self):
        # Méthode de la classe MobileOperator
        pass

    def doThis(self):
        # Méthode de la classe MobileOperator
        pass

    def doThat(self):
        # Méthode de la classe MobileOperator
        pass

class PygameEnv:
    def __init__(self):
        # Initialisation de la classe MobileSupervisor
        pass


    # Fonction pour dessiner les sous-zones en damier
    def draw_subzones(self, pygame, fenetre, vert, jaune, num_subzones_grid_height, centres_sous_zones, plage_coords, subzones_width, taille_case_x, taille_case_y ):
        couleur1 = jaune
        couleur2 = vert

        for i, centre in enumerate(centres_sous_zones):

            if i % 2 == 0 : couleur = couleur1
            else : couleur = couleur2

            for dx in range(plage_coords[0], plage_coords[subzones_width -1] + 1):
                for dy in range(plage_coords[0], plage_coords[subzones_width -1] + 1):
                    x = centre[0] + dx
                    y = centre[1] + dy
                    pygame.draw.rect(fenetre, couleur, (x * taille_case_x, y * taille_case_y, taille_case_x, taille_case_y))

            multiple = (i+1) % num_subzones_grid_height
            if multiple == 0  :
                temp = couleur1
                couleur1 = couleur2
                couleur2 = temp


    # Fonction pour dessiner les sous-zones visités
    def draw_visited_subzones(self, pygame, fenetre, orange, centres_sous_zones_visitees, plage_coords, subzones_width, taille_case_x, taille_case_y ):

        for centre in centres_sous_zones_visitees:
            for dx in range(plage_coords[0], plage_coords[subzones_width -1] + 1):
                for dy in range(plage_coords[0], plage_coords[subzones_width -1] + 1):
                    x = centre[0] + dx
                    y = centre[1] + dy
                    pygame.draw.rect(fenetre, orange, (x * taille_case_x, y * taille_case_y, taille_case_x, taille_case_y))


    # Fonction pour dessiner la grille
    def draw_grid(self, pygame, fenetre, noir, hauteur_fenetre, largeur_fenetre, taille_case_x, taille_case_y):
        for x in range(0, largeur_fenetre, taille_case_x):
            pygame.draw.line(fenetre, noir, (x, 0), (x, hauteur_fenetre))
        for y in range(0, hauteur_fenetre, taille_case_y):
            pygame.draw.line(fenetre, noir, (0, y), (largeur_fenetre, y))


    # Fonction pour dessiner le supervisor
    def draw_supervisor(self,pygame, fenetre, bleu_clair, mobileSupervisor, taille_case_x, taille_case_y ):
        pygame.draw.rect(fenetre, bleu_clair, (mobileSupervisor.get_x_pos() * taille_case_x, mobileSupervisor.get_y_pos() * taille_case_y, taille_case_x, taille_case_y))


    # Fonction pour dessiner les operators
    def draw_operators(self, pygame, fenetre, bleu_fonce, mobileOperators, taille_case_x, taille_case_y):
        for i in range(len(mobileOperators)):
            pygame.draw.rect(fenetre, bleu_fonce, (mobileOperators[i].get_x_pos() * taille_case_x, mobileOperators[i].get_y_pos() * taille_case_y, taille_case_x, taille_case_y))



    # Fonction pour dessiner une croix
    def draw_crosses(self, pygame, fenetre, rouge, croix, taille_case_x, taille_case_y):
        for x, y in croix:
            x_pos = x * taille_case_x + taille_case_x // 2
            y_pos = y * taille_case_y + taille_case_y // 2

            pygame.draw.line(fenetre, rouge, (x_pos - 10, y_pos - 10), (x_pos + 10, y_pos + 10), 2)
            pygame.draw.line(fenetre, rouge, (x_pos + 10, y_pos - 10), (x_pos - 10, y_pos + 10), 2)




# Définition de l'environnement du problème
class MultiAgentsSupervisorOperatorsEnv(MultiAgentEnv):
    def __init__(self, env_config):
        #print("=================================__init__=================================")
        # Initialisation de l'environnement avec les paramètres de env_config
        self.grid_size = (5, 5)  # Taille de la grille (5x5)


        self.agent_positions = {
            "superviseur": (0, 0),  # Agent avec le rôle 1 (superviseur) commence en haut à gauche
            "agent_1": (0, 0),     # Agents avec le rôle 2 commencent également en haut à gauche
            "agent_2": (0, 0),
            "agent_3": (0, 0),
        }

        self.subzones_width = env_config["subzones_width"]
        centre = self.subzones_width // 2
        self.plage_coords = [i - centre for i in range(self.subzones_width)] # plage de coordonnées utile pour dessiner les sous-zones

        self.num_subzones_grid_width = env_config["num_boxes_grid_width"] // self.subzones_width
        self.num_subzones_grid_height = env_config["num_boxes_grid_height"] // self.subzones_width
        self.num_subzones = self.num_subzones_grid_width * self.num_subzones_grid_height

        self.num_operators = env_config["num_operators"]
        self.num_directions = env_config["num_directions"]
        self.num_targets = env_config["num_targets"]

        # Taille de la grille
        self.largeur_grille = env_config["num_boxes_grid_width"] #Nombre de colonnes de la grille
        self.hauteur_grille = env_config["num_boxes_grid_height"]  #Nombre de lignes de la grille


        self.agents_ids = ["supervisor","operator_0","operator_1","operator_2"]

        supervisor= MobileSupervisor()
        operator_0=MobileOperator()
        operator_1=MobileOperator()
        operator_2=MobileOperator()
        self.mobile_agents = {self.agents_ids[0] : supervisor , self.agents_ids[1] : operator_0  ,self.agents_ids[2] : operator_1, self.agents_ids[3] : operator_2 }





        self.supervisor_visited_subzones = []  # Stocker les sous-zones visitées par le supervisor
        self.operator_visited_points = [[] for _ in range(self.num_operators)]  # Stocker les points visités par chaque operator

        ############################################################################################
        # Dimensions de la fenêtre pygame
        self.largeur_fenetre = env_config["num_boxes_grid_width"] * 40
        self.hauteur_fenetre = env_config["num_boxes_grid_height"] * 40


        self.goal_positions = {
            self.agents_ids[0]: (self.largeur_grille - 1, 0),  # Objectif du superviseur : coin supérieur droit
            self.agents_ids[1]: (self.largeur_grille - 1, self.hauteur_grille - 1),  # Objectif des agents 1, 2 et 3 : coin inférieur droit
            self.agents_ids[2]: (self.largeur_grille - 1, self.hauteur_grille - 1),
            self.agents_ids[3]: (self.largeur_grille - 1, self.hauteur_grille - 1),
            }
            #         self.agents_ids[0]: (self.largeur_grille - 1, 0),  # Objectif du superviseur : coin supérieur droit
            # self.agents_ids[1]: (self.largeur_grille - 1, self.hauteur_grille - 1),  # Objectif des agents 1, 2 et 3 : coin inférieur droit
            # self.agents_ids[2]: (self.largeur_grille - 1, self.hauteur_grille - 1),
            # self.agents_ids[3]: (self.largeur_grille - 1, self.hauteur_grille - 1),



        # Taille de la case
        self.taille_case_x = self.largeur_fenetre // self.largeur_grille
        self.taille_case_y = self.hauteur_fenetre // self.hauteur_grille

        # Initialisation de la liste de coordonnées des centres des sous-zones jaunes et vertes
        self.centres_sous_zones = []
        pas = env_config["subzones_width"]
        # Boucles pour générer les coordonnées
        for x in range(1, self.largeur_grille, pas):
            for y in range(1, self.hauteur_grille, pas):
                self.centres_sous_zones.append((x, y))


        # Initialisation de la liste de coordonnées des sous-zones visitées pour l'exemple
        self.centres_sous_zones_visitees = []
        self.centres_sous_zones_visitees = self.centres_sous_zones[0:2]

        self.mobileSupervisor= MobileSupervisor()
        # Position du supervisor à l'itération 0
        self.mobileSupervisor.set_x_pos(0)
        self.mobileSupervisor.set_y_pos(0)

        self.mobileOperators = [MobileOperator() for _ in range(self.num_operators)]

        # Positions des operators à l'itération 0
        for i in range(self.num_operators):
            self.mobileOperators[i].set_x_pos(0)
            self.mobileOperators[i].set_y_pos(0)



        # Liste de croix représentant la case où se trouvent les cibles
        self.croix = []
        # Générer 60 croix aléatoirement
        for _ in range(self.num_targets):
            x = random.randint(0, self.largeur_grille - 1)
            y = random.randint(0, self.hauteur_grille - 1)
            self.croix.append((x, y))
        super().__init__()
        ############################################################################################

        #print(self.observation_space)
    def reset(self):
       # print("=================================reset=================================")
        #print("reset")
        
        self.step_counter=0



        # Positions des _agents à l'itération 0
        for id in self.agents_ids:
            self.mobile_agents[id].set_x_pos(0)
            self.mobile_agents[id].set_y_pos(0)

        self.goal_positions = {
            self.agents_ids[0]: (self.largeur_grille - 1, 0),  # Objectif du superviseur : coin supérieur droit
            self.agents_ids[1]: (self.largeur_grille - 1, self.hauteur_grille - 1),  # Objectif des agents 1, 2 et 3 : coin inférieur droit
            self.agents_ids[2]: (self.largeur_grille - 1, self.hauteur_grille - 1),
            self.agents_ids[3]: (self.largeur_grille - 1, self.hauteur_grille - 1),
            }
        observations={ self.agents_ids[0]:None,
            self.agents_ids[1]:None,
            self.agents_ids[2]:None,
            self.agents_ids[3]:None,
            }
        for id in self.agents_ids:
            observations[id] = self._get_observation(id)

        #print(observations)
        return observations

    def step(self, action_dict):
        finish=0
        self.step_counter+=1
        #print("step numbrer = " + str(self.step_counter))

        observations={self.agents_ids[0]:None,
                    self.agents_ids[1]:None,
                    self.agents_ids[2]:None,
                    self.agents_ids[3]:None, }

        rewards={self.agents_ids[0]:None,
                self.agents_ids[1]:None,
                self.agents_ids[2]:None,
                self.agents_ids[3]:None,}

        terminateds={self.agents_ids[0]:None,
                self.agents_ids[1]:None,
                self.agents_ids[2]:None,
                self.agents_ids[3]:None,
                "__all__" : False }

        infos={self.agents_ids[0]:None,
            self.agents_ids[1]:None,
            self.agents_ids[2]:None,
            self.agents_ids[3]:None,}


   
        for agent_id, action in action_dict.items():

            pre_x = self.mobile_agents[agent_id].get_x_pos()
            pre_y =self.mobile_agents[agent_id].get_y_pos()


            if action == 0:  # UP
                self.mobile_agents[agent_id].set_y_pos(min(self.hauteur_grille-1, pre_y+1))
            elif action == 1:  # DOWN
                self.mobile_agents[agent_id].set_y_pos(max(0, pre_y-1 ))
            elif action == 2:  # LEFT
                self.mobile_agents[agent_id].set_x_pos(max(0, pre_x-1))
            elif action == 3:  # RIGHT
                self.mobile_agents[agent_id].set_x_pos(min(self.largeur_grille-1, pre_x+1))
            else:
                raise Exception("action: {action} is invalid")
           
            now_x = self.mobile_agents[agent_id].get_x_pos()
            now_y =self.mobile_agents[agent_id].get_y_pos()
           
            if self.goal_positions[agent_id] == (now_x, now_y) :
                #print("win")
                terminateds[agent_id]=True
                rewards[agent_id]=1000
                
            else :
                terminateds[agent_id]=False
                rewards[agent_id]=-1
            if self.step_counter >= 500:
                #print("lose")
                rewards[agent_id]=-1000
                terminateds["__all__"]=True
            infos[agent_id]={}
            observations[agent_id]=self._get_observation(agent_id)
            
       
        for id in self.agents_ids : 
            if terminateds[id] == None : 
                del observations[id]
                del rewards[id] 
                del terminateds[id] 
                del infos[id] 
                finish+=1

        if finish==4 : 
            terminateds["__all__"]=True

        #print("observations" + str(observations))
        #print("rewards"+ str(rewards))
        #print("terminateds"+ str(terminateds))
    
        #print("infos"+ str(infos))
        #print("")
        
        return observations, rewards, terminateds, infos

    def _get_observation(self,agent_id):

        # L'observation dépend de la position actuelle de chaque agent
        observation =   [self.mobile_agents[agent_id].get_x_pos(),
                         self.mobile_agents[agent_id].get_y_pos(),
                         self.goal_positions[agent_id][0],
                         self.goal_positions[agent_id][1]]

        return observation


    # Dans la classe MultiAgentClusterEnv, modifiez la méthode render pour afficher la grille, les robots, les points et les subzones
    def render(self):
        # Initialisation de Pygame
        pygame.init()

        pygameEnv = PygameEnv()

        # Création de la fenêtre
        fenetre = pygame.display.set_mode((self.largeur_fenetre, self.hauteur_fenetre))
        pygame.display.set_caption("Multi-Agent Supervisor Workers Environment")

        # Couleurs
        blanc = (255, 255, 255)
        noir = (0, 0, 0)
        bleu_clair = (173, 216, 230)
        bleu_fonce = (0, 0, 128)
        rouge = (255, 0, 0)
        jaune = (255, 255, 0)
        vert = (0, 255, 0)
        orange = (255, 128, 0)

        clock = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()

            if self.num_directions == 4 :
                # Déplacement aléatoire du supervisor
                direction_supervisor = random.choice(["up", "down", "left", "right"])
                supervisor_y = self.mobileSupervisor.get_y_pos()
                supervisor_x = self.mobileSupervisor.get_x_pos()
                if direction_supervisor == "up" and supervisor_y > 0:
                    self.mobileSupervisor.set_y_pos(supervisor_y -1)
                elif direction_supervisor == "down" and supervisor_y < self.hauteur_grille - 1:
                    self.mobileSupervisor.set_y_pos(supervisor_y + 1)
                elif direction_supervisor == "left" and supervisor_x > 0:
                    self.mobileSupervisor.set_x_pos(supervisor_x - 1)
                elif direction_supervisor == "right" and supervisor_x < self.largeur_grille - 1:
                    self.mobileSupervisor.set_y_pos(supervisor_x + 1)

                # Déplacement aléatoire des operators
                for i in range(self.num_operators):
                    direction_operator = random.choice(["up", "down", "left", "right"])
                    operator_x = self.mobileOperators[i].get_x_pos()
                    operator_y = self.mobileOperators[i].get_y_pos()
                    if direction_operator == "up" and operator_y > 0:
                        self.mobileOperators[i].set_y_pos(operator_y - 1)
                    elif direction_operator == "down" and operator_y < self.hauteur_grille - 1:
                        self.mobileOperators[i].set_y_pos(operator_y + 1)
                    elif direction_operator == "left" and operator_x > 0:
                        self.mobileOperators[i].set_x_pos(operator_x - 1)
                    elif direction_operator == "right" and operator_x < self.largeur_grille - 1:
                        self.mobileOperators[i].set_x_pos(operator_x + 1)

            elif self.num_directions == 8:
                # Déplacement aléatoire du supervisor
                direction_supervisor = random.choice(["up", "down", "left", "right", "diag_sup_left", "diag_sup_right", "diag_sup_left", "diag_sup_right"])
                supervisor_y = self.mobileSupervisor.get_y_pos()
                supervisor_x = self.mobileSupervisor.get_x_pos()
                if direction_supervisor == "up" and supervisor_y > 0:
                    self.mobileSupervisor.set_y_pos(supervisor_y -1)
                elif direction_supervisor == "down" and supervisor_y < self.hauteur_grille - 1:
                    self.mobileSupervisor.set_y_pos(supervisor_y + 1)
                elif direction_supervisor == "left" and supervisor_x > 0:
                    self.mobileSupervisor.set_x_pos(supervisor_x - 1)
                elif direction_supervisor == "right" and supervisor_x < self.largeur_grille - 1:
                    self.mobileSupervisor.set_y_pos(supervisor_x + 1)
                elif direction_supervisor == "diag_sup_left" and (supervisor_x > 0) and (supervisor_y > 0):
                    self.mobileSupervisor.set_x_pos(supervisor_x - 1)
                    self.mobileSupervisor.set_y_pos(supervisor_y - 1)
                elif direction_supervisor == "diag_sup_right" and (supervisor_x < self.largeur_grille - 1) and (supervisor_y > 0):
                    self.mobileSupervisor.set_x_pos(supervisor_x + 1)
                    self.mobileSupervisor.set_y_pos(supervisor_y - 1)
                elif direction_supervisor == "diag_inf_left" and (supervisor_x > 0) and (supervisor_y < self.hauteur_grille - 1):
                    self.mobileSupervisor.set_x_pos(supervisor_x - 1)
                    self.mobileSupervisor.set_y_pos(supervisor_y + 1)
                elif direction_supervisor == "diag_inf_right" and (supervisor_x < self.largeur_grille - 1) and (supervisor_y < self.hauteur_grille - 1):
                    self.mobileSupervisor.set_x_pos(supervisor_x + 1)
                    self.mobileSupervisor.set_y_pos(supervisor_y + 1)


                # Déplacement aléatoire des operators
                for i in range(self.num_operators):
                    direction_operator = random.choice(["up", "down", "left", "right", "diag_sup_left", "diag_sup_right", "diag_inf_left", "diag_inf_right"])
                    operator_x = self.mobileOperators[i].get_x_pos()
                    operator_y = self.mobileOperators[i].get_y_pos()
                    if direction_operator == "up" and operator_y > 0:
                        self.mobileOperators[i].set_y_pos(operator_y - 1)
                    elif direction_operator == "down" and operator_y < self.hauteur_grille - 1:
                        self.mobileOperators[i].set_y_pos(operator_y + 1)
                    elif direction_operator == "left" and operator_x > 0:
                        self.mobileOperators[i].set_x_pos(operator_x - 1)
                    elif direction_operator == "right" and operator_x < self.largeur_grille - 1:
                        self.mobileOperators[i].set_x_pos(operator_x + 1)
                    elif direction_operator == "diag_sup_left" and (operator_x > 0) and (operator_y > 0):
                        self.mobileOperators[i].set_x_pos(operator_x - 1)
                        self.mobileOperators[i].set_y_pos(operator_y - 1)
                    elif direction_operator == "diag_sup_right" and (operator_x < self.largeur_grille - 1) and (operator_y > 0):
                        self.mobileOperators[i].set_x_pos(operator_x + 1)
                        self.mobileOperators[i].set_y_pos(operator_y - 1)
                    elif direction_operator == "diag_inf_left" and (operator_x > 0) and (operator_y < self.hauteur_grille - 1):
                        self.mobileOperators[i].set_x_pos(operator_x - 1)
                        self.mobileOperators[i].set_y_pos(operator_y + 1)
                    elif direction_operator == "diag_inf_right" and (operator_x < self.largeur_grille - 1) and (operator_y < self.hauteur_grille - 1):
                        self.mobileOperators[i].set_x_pos(operator_x + 1)
                        self.mobileOperators[i].set_y_pos(operator_y + 1)



            # Efface la fenêtre
            fenetre.fill(blanc)

            # Dessine les sous-zones en damier
            pygameEnv.draw_subzones(pygame, fenetre, vert, jaune, self.num_subzones_grid_height, self.centres_sous_zones, self.plage_coords, self.subzones_width, self.taille_case_x, self.taille_case_y )

            # Dessine les sous-zones visitées pour l'exemple
            pygameEnv.draw_visited_subzones(pygame, fenetre, orange, self.centres_sous_zones_visitees, self.plage_coords, self.subzones_width, self.taille_case_x, self.taille_case_y )

            # Dessine la grille
            pygameEnv.draw_grid(pygame, fenetre, noir, self.hauteur_fenetre, self.largeur_fenetre, self.taille_case_x, self.taille_case_y)

            # Dessine les robots
            pygameEnv.draw_supervisor(pygame, fenetre, bleu_clair, self.mobileSupervisor, self.taille_case_x, self.taille_case_y )
            pygameEnv.draw_operators(pygame, fenetre, bleu_fonce, self.mobileOperators, self.taille_case_x, self.taille_case_y)

            # Dessine les croix
            pygameEnv.draw_crosses(pygame, fenetre, rouge, self.croix, self.taille_case_x, self.taille_case_y)

            # Met à jour la fenêtre
            pygame.display.flip()

            # Limite la fréquence de rafraîchissement
            clock.tick(1)

    # Fonction pour dessiner les sous-zones en damier
    def draw_subzones(self, fenetre, vert, jaune ):
        couleur1 = jaune
        couleur2 = vert

        for i, centre in enumerate(self.centres_sous_zones):

            if i % 2 == 0 : couleur = couleur1
            else : couleur = couleur2

            for dx in range(self.plage_coords[0], self.plage_coords[self.subzones_width -1] + 1):
                for dy in range(self.plage_coords[0], self.plage_coords[self.subzones_width -1] + 1):
                    x = centre[0] + dx
                    y = centre[1] + dy
                    pygame.draw.rect(fenetre, couleur, (x * self.taille_case_x, y * self.taille_case_y, self.taille_case_x, self.taille_case_y))

            multiple = (i+1) % self.num_subzones_grid_height
            if multiple == 0  :
                temp = couleur1
                couleur1 = couleur2
                couleur2 = temp

    # Fonction pour dessiner les sous-zones visités
    def draw_visited_subzones(self, fenetre, orange ):
        for centre in self.centres_sous_zones_visitees:
            for dx in range(self.plage_coords[0], self.plage_coords[self.subzones_width -1] + 1):
                for dy in range(self.plage_coords[0], self.plage_coords[self.subzones_width -1] + 1):
                    x = centre[0] + dx
                    y = centre[1] + dy
                    pygame.draw.rect(fenetre, orange, (x * self.taille_case_x, y * self.taille_case_y, self.taille_case_x, self.taille_case_y))

    # Fonction pour dessiner la grille
    def draw_grid(self, fenetre, noir):
        for x in range(0, self.largeur_fenetre, self.taille_case_x):
            pygame.draw.line(fenetre, noir, (x, 0), (x, self.hauteur_fenetre))
        for y in range(0, self.hauteur_fenetre, self.taille_case_y):
            pygame.draw.line(fenetre, noir, (0, y), (self.largeur_fenetre, y))



if __name__ == "__main__":

    ray.init()



    # Can also register the env creator function explicitly with:
    # register_env("MultiAgentsSupervisorOperatorsEnv", lambda config: MultiAgentsSupervisorOperatorsEnv(config))





    def select_policy(algorithm, framework):
        if algorithm == "PPO":
            if framework == "torch":
                return PPOTorchPolicy
            elif framework == "tf":
                return PPOTF1Policy
            else:
                return PPOTF2Policy
        else:
            raise ValueError("Unknown algorithm: ", algorithm)


    # Construct two independent Algorithm configs
    ppo_config = (
        PPOConfig()
        # or "corridor" if registered above
        .environment(MultiAgentsSupervisorOperatorsEnv,
                    env_config={
                        "num_boxes_grid_width":24,
                        "num_boxes_grid_height":12,
                        "subzones_width":3,
                        "num_operators": 3,
                        "num_supervisors": 1,
                        "num_directions": 8,
                        "num_targets":60,
                        "__all__": True
                    })
        .environment(disable_env_checking=True)

        .framework("torch")

        # disable filters, otherwise we would need to synchronize those
        # as well to the DQN agent
        .rollouts(observation_filter="MeanStdFilter")
        .training(
            model={"vf_share_layers": True},
            vf_loss_coeff=0.01,
            num_sgd_iter=6,
            _enable_learner_api=False,
        )
        # Use GPUs iff `RLLIB_NUM_GPUS` env var set to > 0.
        .resources(num_gpus=0)
        .rollouts(num_rollout_workers=1)
        .rl_module(_enable_rl_module_api=False)

    )

    #min_x, max_x = 0.0, self.largeur_grille-1  # Exemple de limites pour les coordonnées x
    #min_y, max_y = 0.0, self.hauteur_grille-1   # Exemple de limites pour les coordonnées y

    obs = spaces.Box(low=0, high=24, shape=(4,))
    acti = spaces.Discrete(4)
    policies = {
        "supervisor_policy": (None,obs,acti, {}),# <- use default class & infer obs-/act-spaces from env.
        "operator_policy": (None,obs,acti, {}),# <- use default class & infer obs-/act-spaces from env.
    }
    def policy_mapping_fn(agent_id, episode, worker, **kwargs):
        #print("===============================================================")
        #print(agent_id)
        if agent_id == "supervisor" :
            #print("1")
            return "supervisor_policy"

        else:
            #print("2")
            return "operator_policy"


    ppo_config.multi_agent(
        policies=policies,
        policy_mapping_fn=policy_mapping_fn,
    )
    ppo = ppo_config.build()


    i=0
    intervalle=100
    last_i=0
    while True :
        i+=1

        print("== Iteration", i, "==")
        # improve the PPO policy
        print("-- PPO --")
        result_ppo = ppo.train()
        print(pretty_print(result_ppo))
        if (i-last_i)==intervalle :

            #Pour créer des points de contrôle :
            checkpoint = ppo.save()
            print(checkpoint)

            #Évaluez à tout moment en appelant evaluate.
            #evaluation = ppo.evaluate()
            #print(pretty_print(evaluation))



        # #Restaurez un algorithme à partir d'un points de contrôle
        # restored_algo = Algorithm.from_checkpoint(checkpoint)
