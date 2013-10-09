from os.path import dirname, join

from openmdao.main.api import Assembly

from openmdao.lib.components.api import GeomComponent
from openmdao.lib.datatypes.api import Float, Int

#hyperloop sizing calculations
from inlet import InletGeom 
from battery import Battery
from passenger_capsule import PassengerCapsule
from tube_structure import TubeStructural
from aero import Aero


#overall geometry assembly
class Pod(Assembly): 
    #Inputs
    area_inlet_in = Float(iotype="in", units="cm**2", desc="flow area required at the front of the inlet")
    area_inlet_out = Float(iotype="in", units="cm**2", desc="flow area required at the back of the inlet")
    time_mission = Float(iotype="in", units="s", desc="travel time for a single trip")
    radius_tube_inner = Float(iotype="in", units="cm", desc="inner tube radius")
    rho_air = Float(iotype="in", units="kg/m**3", desc="air density (aero calcs)")
    F_net = Float(iotype="in", desc="Thrust generated by the nozzle", units="N")
    energy = Float(iotype="in", desc="Energy required from batteries", units="kW*h")
    Ps_tube = Float(99, iotype="in", desc="static pressure in the tube", units="Pa")
    speed_max = Float(iotype="in", desc="maximum velocity of the pod", units="m/s")
    hub_to_tip = Float(.4, iotype="in", desc="hub to tip ratio for the compressor")
    coef_drag = Float(2, iotype="in", desc="capsule drag coefficient")
    n_rows = Int(14, iotype="in", desc="number of rows of seats in the pod")
    length_row = Float(150, iotype="in", units="cm", desc="length of each row of seats")
    #Outputs
    radius_inlet_back_outer = Float(iotype="out", units="cm", desc="outer radius of the back of the inlet")
    area_compressor_bypass = Float(iotype="out", units="cm**2", desc="area available to move compressed air around the passenger capsule")
    area_cross_section = Float(iotype="out", units="cm**2", desc="cross sectional area of the passenger capsule")
    radius_tube_outer = Float(iotype="out", units="cm", desc="outer radius of tube")
    net_force = Float(iotype="out", desc="Net force with drag considerations", units="N")
    
    def configure(self): 

        #Add Components
        capsule = self.add('capsule', PassengerCapsule())
        tube = self.add('tube', TubeStructural())
        inlet = self.add('inlet', InletGeom())
        battery = self.add('battery', Battery())
        aero = self.add('aero', Aero())
        
        #Boundary Input Connections
        #Pod -> Capsule
        self.connect('n_rows','capsule.n_rows')
        self.connect('length_row','capsule.length_row')
        #Pod->Tube
        self.connect('radius_tube_inner', 'tube.radius_inner')
        self.connect('Ps_tube', 'tube.Ps_tube')
        #Pod->Inlet
        self.connect('area_inlet_in','inlet.area_in')
        self.connect('area_inlet_out','inlet.area_out')
        self.connect('hub_to_tip','inlet.hub_to_tip')
        #Pod -> Battery
        self.connect('time_mission','battery.time_mission')
        self.connect('energy','battery.energy')
        #Pod -> Aero
        self.connect('coef_drag','aero.coef_drag')
        self.connect('rho_air','aero.rho')
        self.connect('speed_max','aero.velocity_capsule')
        self.connect('F_net','aero.gross_thrust')


        #Inter Component Connections
        #Capsule -> Inlet
        self.connect('capsule.area_cross_section','inlet.area_passenger_capsule')
        #Capsule -> Battery
        self.connect('capsule.area_cross_section','battery.area_cross_section')
        #Inlet -> Aero
        self.connect('inlet.area_frontal','aero.area_capsule')

        #Boundary Output Connections
        #Capsule -> Pod
        self.connect('capsule.area_cross_section','area_cross_section')
        #Tube->Pod
        self.connect('tube.radius_outer','radius_tube_outer')
        #Inlet->Pod
        self.connect('inlet.radius_back_outer', 'radius_inlet_back_outer')
        self.connect('inlet.area_bypass', 'area_compressor_bypass')
        #Aero -> Pod
        self.connect('aero.net_force','net_force')  #not currently used, eventually passed to mission

        #Declare Solver Workflow
        self.driver.workflow.add(['capsule','tube','inlet','battery','aero'])

    def run(self,*args,**kwargs): 
        super(Assembly, self).run(*args,**kwargs)


if __name__ == "__main__": 
    from openmdao.main.api import set_as_top
    g = set_as_top(Pod())
