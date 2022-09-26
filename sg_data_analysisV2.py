from os import listdir
from datetime import date
from env import REPLAYS_PATH, PLAYER_TAGS

def nice_output (input):
    if type(input) == dict:
        input = sorted(input.items(), key=lambda x: x[1], reverse= True)
        output=""
        for i in input:
            output+="{} : {} \n".format(i[0], i[1])

    return output



class Collection:

    def __init__ (self):
        #just defining here the stats i wanna have and then updating them each time a replay is added to the collection via Collection.add()

        #each replay added with Collection.add() will be added to this list, no real use exept keeping a track off all replay, intended to be used if merging multiple Collection object
        self.replays = []

        #how many game played against each character, the most basic stat of all
        self.characters_data = {}

        #how many individual person plays each character
        #this variable ain't updated by Collection.add() but but _get_mains_data()
        #self._mains_data = {}

        #character usage for the player
        self.player_characters_data = {}

        #team usage for the player
        self.player_team_data={}

        #number of time opponent was faced
        self.opponents_data = {}

        #character usage for each opponent
        self.opponents_characters_data= {}

        #team usage for each opponent
        self.opponents_team_data={}

        #self-explanatory 
        self.stage_data = {}

        #how many replay don't have a player identified, intended for debug and making it easier to find your old tags
        self.no_player_replay = 0


    def add(self, replay):
        #Checks that repaly is a Replay object
        if not isinstance(replay, Replay):
            raise ValueError("You must pass an 'Replay' object to Collection.add() function")

        self.replays.append(replay)

        #update self.stage_data
        self.stage_data = self._safe_incremental(self.stage_data, replay.stage)

        #Checks if the player has been identified in this replay
        if len(replay.opponents) == 2:
            self.no_player_replay += 1
        #If it's the case then update the player data
        else :
            for p in replay.player:
                #update self.player_characters_data
                for char in p["TEAM"]:
                    self.player_characters_data = self._safe_incremental(self.player_characters_data, char[0])

                #update self.player_team_data
                self.player_team_data = self._safe_incremental(self.player_team_data, self._team_to_str(p["TEAM"]))

        for opponent in replay.opponents :
            for char in opponent["TEAM"]:
                #updating self.characters_data
                self.characters_data = self._safe_incremental(self.characters_data, char[0])
                #updating self.opponents_characters_data
                if self.opponents_characters_data.get(opponent["TAG"]) == None:
                    self.opponents_characters_data[opponent["TAG"]] = {}
                self.opponents_characters_data[opponent["TAG"]] = self._safe_incremental(self.opponents_characters_data[opponent["TAG"]], char[0])

            #updating self.opponents_data
            self.opponent_data = self._safe_incremental(self.opponents_data, opponent["TAG"])
            #updating self.opponents_team_data
            if self.opponents_team_data.get(opponent["TAG"]) == None:
                    self.opponents_team_data[opponent["TAG"]] = {}
            self.opponents_team_data[opponent["TAG"]] = self._safe_incremental(self.opponents_team_data[opponent["TAG"]], self._team_to_str(opponent["TEAM"]))


    def get_data_ignoring(self, tag):
        new_characters_data = self.characters_data
        try:
            for char in self.opponents_characters_data[tag]:
                new_characters_data[char] = new_characters_data[char] - self.opponents_characters_data[tag][char]
            return new_characters_data
        except KeyError:
            raise ValueError("This player doesn't exist in the collection")

    #called when Collection.mains_data is used (using python property system)
    def _get_mains_data(self):
        mains_data={}
        for (player, chars) in self.opponents_characters_data.items() :
            for char in chars:
                mains_data = self._safe_incremental(mains_data, char)
        return mains_data

    #increase by 1 a value of a dict
    def _safe_incremental(self, dict, key):
        try:
            dict[key] += 1
        except KeyError:
            dict[key] =1

        return dict


    #turns a "team" into a pretty string
    def _team_to_str(self, team):
        if len(team) == 1:
            return f"Solo {team[0][0]}"
        else:
            str_team =""
            for char in team:
                str_team +=  f"{char[0]}, "
            return str_team[:-2]

    mains_data = property(fget=_get_mains_data)

class Replay:

    def __init__(self, replay_file, player_tags=[]):
        #get the replay data and parse it
        with open(REPLAYS_PATH+replay_file, "r") as opened_file:
            self._parse_the_data(opened_file.read())

        #if a player tag is given splits the data into self.player and and self.opponent (if if not both player data will be stocked in self.opponent)
        if player_tags != []:
            self.player = []
            for tag in player_tags:
                self.player += [i for i in self.opponents if i["TAG"] == tag]
                self.opponents = [i for i in self.opponents if i["TAG"] != tag]


    def  __str__ (self):
        if len(self.opponents) == 2:
            return str({
                "STAGE" : self.stage,
                "PLAYER1": {"TAG": self.opponents[0]["TAG"], "TEAM": self.opponents[0]["TEAM"], "TEAM_SIZE": self.opponents[0]["TEAM_SIZE"]},
                "PLAYER2": {"TAG": self.opponents[1]["TAG"], "TEAM": self.opponents[1]["TEAM"], "TEAM_SIZE": self.opponents[1]["TEAM_SIZE"]}
            })
        else:
            return str({
                "STAGE" : self.stage,
                "PLAYER": {"TAG": self.player[0]["TAG"], "TEAM": self.player[0]["TEAM"], "TEAM_SIZE": self.player[0]["TEAM_SIZE"]},
                "OPPONENT": {"TAG": self.opponents[0]["TAG"], "TEAM": self.opponents[0]["TEAM"], "TEAM_SIZE": self.opponents[0]["TEAM_SIZE"]}
            })


    #parsing replay file to something useable
    def _parse_the_data (self, data) :
        p1_start = data.find("Player 1")
        p2_start = data.find("Player 2") 
        p1_name_start = data.find("P1Name")

        self.opponents = []
        for player_data in (data[p1_start:p2_start] , data[p2_start:p1_name_start]):
            parsed_player_data = {"TEAM": []}
            parsing = player_data.split("\n")

            parsed_player_data["TEAM_SIZE"] = 1
            parsed_player_data["TEAM"].append((parsing[1].split(" ")[1], parsing[2]))
            if len(parsing) >= 10:
                parsed_player_data["TEAM_SIZE"] = 2
                parsed_player_data["TEAM"].append((parsing[5].split(" ")[1], parsing[6]))
                if len(parsing) == 14:
                    parsed_player_data["TEAM_SIZE"] = 3
                    parsed_player_data["TEAM"].append((parsing[9].split(" ")[1], parsing[10]))

            self.opponents.append(parsed_player_data)

        self.opponents[0]["TAG"] = data[p1_name_start:].split("\n")[0][7:]
        self.opponents[1]["TAG"] = data[p1_name_start:].split("\n")[1][7:]
        self.stage = data[6:data.find("NumRounds")-1].replace("_", " ")
        #empty stages starts with an '_' wich is being replace by a space and its not ESTETHIC so i just remove it lmao, nothing to see here
        if self.stage[0] == " ":
            self.stage = self.stage[1:]



#actually doing shit
replay_files_ls = [f for f in listdir(REPLAYS_PATH) if f[-3:] == "ini"]

TheCore = Collection()
for i in replay_files_ls:
    TheCore.add(Replay(i, PLAYER_TAGS))

output=""
output += f"Number of replay used for this data: {len(TheCore.replays)}\n"
output += f"\nGeneral character usage: \n\n{nice_output(TheCore.characters_data)}"
output += f"\n\nPlayer character usage: \n\n{nice_output(TheCore.player_characters_data)}"
output += f"\n\nPlayer team usage: \n\n{nice_output(TheCore.player_team_data)}"
output += f"\n\nOpponents faced: \n\n{nice_output(TheCore.opponents_data)}"
output += f"\n\nHow many different player play those characters: \n\n{nice_output(TheCore.mains_data)}"
output += f"\n\nStage usage: \n\n{nice_output(TheCore.stage_data)}"

#the kind of data you can have of one specific opponent
output += f"\nGeneral character usage without XXX: \n\n{nice_output(TheCore.get_data_ignoring('XXX'))}"
output += f"\n\nXXX character usage: \n\n{nice_output(TheCore.opponents_characters_data['XXX'])}"
output += f"\n\nXXX team usage: \n\n{nice_output(TheCore.opponents_team_data['XXX'])}"

f = open(f"./stats-{date.today()}.txt", "w")
f.write(output)
f.close()