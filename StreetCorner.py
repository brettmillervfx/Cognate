import agent
import world
import ai


if __name__ == "__main__":
    '''
    All of this lives in our "game thread"
    '''
    
    max_tick = 50
    curr_tick = 0
    queue_process_limit = 3

    w = world.World()
 
    thief = agent.Agent()
    cop = agent.Agent()
    bag_lady = agent.Agent()
    skater = agent.Agent()

    w = world.World()

    ai_manager = ai.AiManager()
    ai_manager.set_world(w)

    thief.register(ai_manager)
    cop.register(ai_manager)
    bag_lady.register(ai_manager)
    skater.register(ai_manager)

    thief.init()
    cop.init()
    bag_lady.init()
    skater.init()

    agents = [thief, cop, bag_lady, skater]

    while curr_tick < max_tick:
        events = w.advance()
        for event in events:
            print(event)
        ai_manager.process(queue_process_limit)


