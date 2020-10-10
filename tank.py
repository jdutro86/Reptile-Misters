"""tank.py
Contains all tank-logic related objects
"""

# Contains information for a single lizard
class Lizard(object):
    def __init__(self, species, gender, name=''):
        self.species = species
        self.gender = gender
        self.name = name

# List wrapper class for lizards, allows function chaining
# i.e. lizards.of_gender(...).of_species(...).of_name(...)
class Lizards(list):
    # gets lizards with matching name
    def of_name(self, name):
        filter = lambda x: x.name == name
        return self.of_filter(filter)

    # gets lizards with matching gender
    def of_gender(self, gender):
        filter = lambda x: x.gender == gender
        return self.of_filter(filter)

    # gets lizards with matching species
    def of_species(self, species):
        filter = lambda x: x.species == species
        return self.of_filter(filter)

    # gets lizards with matching filter
    def of_filter(self, filter):
        return Lizards([i for i in self if filter(i)])

# Contains information for a single lizard tank
class Tank(object):
    # FLOW_RATE should be in volume per second
    FLOW_RATE = 0

    @staticmethod
    def set_flow_rate(val):
        Tank.FLOW_RATE = val

    def __init__(self, tankVolume=1, expectedWater=1, lizards=Lizards()):
        self.tankVolume = tankVolume
        self.expectedWater = expectedWater
        self.currentWater = 0
        self.lizards = lizards

    # get number of lizards
    def num_lizards(self):
        return len(self.lizards)

    # can pass in single Lizard object or Lizards object
    def add_lizard(self, lizard):
        if isinstance(lizard, Lizard) and lizard not in self.lizards:
            self.lizards.append(lizard)
        elif isinstance(lizard, Lizards):
            for i in lizard:
                self.add_lizard(i)
        else:
            raise ValueError('Value is not a lizard or already exists in lizards!')

    # can pass in single Lizard object or Lizards object
    def remove_lizard(self, lizard):
        if isinstance(lizard, Lizard) and lizard in self.lizards:
            self.lizards.remove(lizard)
        elif isinstance(lizard, Lizards):
            for i in lizard:
                self.remove_lizard(i)
        else:
            raise ValueError('Value is not a lizard or does not exist in lizards!')

    # fill tank slightly
    def update(self, dt):
        self.currentWater += Tank.FLOW_RATE * dt

    # fully drain tank
    def drain(self):
        self.currentWater = 0

    # get fraction of tank expected water that has been given
    def get_fraction(self):
        return self.currentWater / self.expectedWater
