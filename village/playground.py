from village.pybpodapi.protocol import Bpod, StateMachine

bpod = Bpod()
sma = StateMachine(bpod)


sma.add_state(
    state_name="State0",
    state_timer=3,
    state_change_conditions={Bpod.Events.Tup: "exit"},
    output_actions=[],
)

# sma.add_state(
#     state_name='State1',
#     state_timer=0,
#     state_change_conditions={'Port1In': 'State2'},
#     output_actions=[(Bpod.OutputChannels.LED, 1)]
# )

# sma.add_state(
#     state_name='State2',
#     state_timer=0,
#     state_change_conditions={'Port1Out': 'State1'},
#     output_actions=[]
# )

bpod.send_state_machine(sma)
bpod.run_state_machine(sma)
