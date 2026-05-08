import asyncio
import random
import time
from argparse import ArgumentParser

from playground import playgrounds
from sport_api import FudanAPI, get_routes


async def main():
    parser = ArgumentParser()
    parser.add_argument('-v', '--view', action='store_true', help="list available routes")
    parser.add_argument('-r', '--route', help="set route ID", type=int)
    parser.add_argument('-t', '--time', help="total time, in seconds", type=int)
    parser.add_argument('-d', '--distance', help="total distance, in meters", type=int)
    parser.add_argument('-q', '--delay', action='store_true', help="delay for random time")
    args = parser.parse_args()

    if args.view:
        routes = await get_routes()
        supported_routes = filter(lambda r: r.id in playgrounds, routes)
        for route in supported_routes:
            route.pretty_print()
        exit()

    if args.route:
        # set distance
        distance = 1200
        if args.distance:
            distance = args.distance
        distance += random.uniform(-5.0, 25.0)

        # set time
        total_time = 300
        if args.time:
            total_time = args.time
        total_time += random.uniform(-10.0, 10.0)

        # get routes from server
        routes = await get_routes()
        for route in routes:
            if route.id == args.route:
                selected_route = route
                break
        else:
            raise ValueError(f'不存在id为{args.route}的route')

        # delay random time, used in GitHub Action deployment
        if args.delay:
            sleep_time = random.randint(0, 240)
            time.sleep(sleep_time)

        # prepare & start running
        automator = FudanAPI(selected_route)
        playground = playgrounds[args.route]
        current_distance = 0
        await automator.start()
        print(f"START: {selected_route.name}")
        while current_distance < distance:
            current_distance += distance / total_time
            message, _ = await asyncio.gather(
                automator.update(playground.random_offset(current_distance)), asyncio.sleep(1))
            print(f"UPDATE: {message} ({current_distance}m / {distance}m)")
        finish_message = await automator.finish(playground.coordinate(distance))
        print(f"FINISHED: {finish_message}")

if __name__ == '__main__':
    asyncio.run(main())
