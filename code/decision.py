import numpy as np


# This is where you can build a decision tree for determining throttle, brake and steer 
# commands based on the output of the perception_step() function
# Actually, I am used to state machine in my daily work, so I translate into that way
class State:
    def run(self):
        assert 0, "run not implemented"
    def next(self, input):
        assert 0, "next not implemented"
	
class StateMachine:
    def __init__(self, initialState):
        self.currentState = initialState
        self.currentState.run()
    # Template method:
    def runAll(self, inputs):
        for i in inputs:
            print(i)
            self.currentState = self.currentState.next(i)
            self.currentState.run()

class Exploring(State):
    def run(self,Rover):
        # Check the extent of navigable terrain
        if Rover.nav_dists**2 >= Rover.stop_forward:  
            # If mode is forward, navigable terrain looks good 
            # and velocity is below max, then throttle 
            # Set throttle value to throttle setting
			Rover.exp_Vel = 2.0
            Rover.throttle = 0.1*(Rover.exp_Vel - Rover.vel)
			Rover.throttle = np.clip(Rover.throttle,0,0.2)
            Rover.brake = 0
            # Set steering to average angle clipped to the range +/- 15
			offset = 1.5
            Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi)+offset, -8, 8) #need a offset here to do the wall crawling
        # If there's a lack of navigable terrain pixels then go to 'stop' mode

    def next(self, Rover):
	if Rover.nav_dists**2 >= Rover.stop_forward:
		elif Rover.nav_dists**2 < Rover.stop_forward:
            # Set mode to "stop" and hit the brakes!
            Rover.throttle = 0
            # Set brake to stored brake value
            Rover.brake = Rover.brake_set
            Rover.steer = 0
            Rover.mode = 'stop'
        if input == MouseAction.removed:
            return MouseTrap.waiting
        return MouseTrap.holding

class RoverRunningState(StateMachine):
    def __init__(self):
        # Initial state
        StateMachine.__init__(self, RoverState.Exploring)

# Static variable initialization:
RoverState.exploring = Exploring()
RoverState.exploring = Exploring()
RoverState.exploring = Exploring()
RoverState.exploring = Exploring()


RoverState().runAll(map(MouseAction, moves))



def decision_step(Rover):

    # Implement conditionals to decide what to do given perception data
    # Here you're all set up with some basic functionality but you'll need to
    # improve on this decision tree to do a good job of navigating autonomously!

    # Example:
    # Check if we have vision data to make decisions with
    if Rover.nav_angles is not None:
        # Check for Rover.mode status
        if Rover.mode == 'forward': 
            # Check the extent of navigable terrain
            if Rover.nav_dists**2 >= Rover.stop_forward:  
                # If mode is forward, navigable terrain looks good 
                # and velocity is below max, then throttle 
                if Rover.vel < Rover.max_vel:
                    # Set throttle value to throttle setting
                    Rover.throttle = Rover.throttle_set
                else: # Else coast
                    Rover.throttle = 0
                Rover.brake = 0
                # Set steering to average angle clipped to the range +/- 15
                Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi)+3, -8, 8)
            # If there's a lack of navigable terrain pixels then go to 'stop' mode
            elif Rover.nav_dists**2 < Rover.stop_forward:
                    # Set mode to "stop" and hit the brakes!
                    Rover.throttle = 0
                    # Set brake to stored brake value
                    Rover.brake = Rover.brake_set
                    Rover.steer = 0
                    Rover.mode = 'stop'

        # If we're already in "stop" mode then make different decisions
        elif Rover.mode == 'stop':
            # If we're in stop mode but still moving keep braking
            if Rover.vel > 0.5:
                Rover.throttle = 0
                Rover.brake = Rover.brake_set
                Rover.steer = -15
            # If we're not moving (vel < 0.2) then do something else
            else:
                Rover.vel <= 0.5
                # Now we're stopped and we have vision data to see if there's a path forward
                if Rover.nav_dists**2 < Rover.go_forward:
                    Rover.throttle = 0
                    # Release the brake to allow turning
                    Rover.brake = 0
                    # Turn range is +/- 15 degrees, when stopped the next line will induce 4-wheel turning
                    Rover.steer = -15 # Could be more clever here about which way to turn
                # If we're stopped but see sufficient navigable terrain in front then go!
                if Rover.nav_dists**2 >= Rover.go_forward:
                    # Set throttle back to stored value
                    Rover.throttle = Rover.throttle_set
                    # Release the brake
                    Rover.brake = 0
                    # Set steer to mean angle
                    Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi), -15, 15)
                    Rover.mode = 'forward'
    # Just to make the rover do something 
    # even if no modifications have been made to the code
    else:
        Rover.throttle = Rover.throttle_set
        Rover.steer = 0
        Rover.brake = 0
        
    # If in a state where want to pickup a rock send pickup command
    if Rover.near_sample and Rover.vel == 0 and not Rover.picking_up:
        Rover.send_pickup = True
    
    return Rover

