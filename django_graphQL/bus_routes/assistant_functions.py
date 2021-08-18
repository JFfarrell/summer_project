import datetime
import pytz
from .schema import *
import pickle


def seconds_to_timestamp(time_in_seconds):
    second = str(int(time_in_seconds % 60))
    remainder = time_in_seconds // 60
    minute = str(int(remainder % 60))
    hour = str(int(remainder // 60))

    return correcting_midnight(leading_0_timestamp(hour, minute, second))


def leading_0_timestamp(hour, minute, second):
    # eliminate single digits in timestamp
    if len(hour) == 1:
        hour = f"0{hour}"
    if len(minute) == 1:
        minute = f"0{minute}"
    if len(second) == 1:
        second = f"0{second}"
    return hour + ":" + minute + ":" + second


def unit_to_seconds(hour, minute):
    ftr = [3600, 60, 1]
    total_secs = (int(hour) * ftr[0]) + (int(minute[1]) * ftr[1])

    return total_secs


def timestamp_to_seconds(time_list):
    ftr = [3600, 60, 1]
    times_in_seconds = []

    for time in time_list:
        time_units = time.split(':')
        total_secs = (int(time_units[0]) * ftr[0]) + (int(time_units[1]) * ftr[1]) + (int(time_units[0]) * ftr[2])
        times_in_seconds.append(total_secs)

    times_in_seconds.sort()
    return times_in_seconds


def departure_times(route, direction):
    all_departure_times = []

    # check every route and assess its departure times vs user's inputted time
    for unique_route in UniqueRoutes.objects.all():
        if unique_route.line_id == route and unique_route.direction == direction:
            dep_time = unique_route.first_departure_schedule.split(',')
            for time in dep_time:
                time = time.strip(" ")
                # preventing error thrown when time returned passes midnight
                time = correcting_midnight(time)
                all_departure_times.append(time)

    return all_departure_times


def return_weather(weather, time, current_day):
    hour = time.split(":")[0].strip("0")
    key = str(current_day) + "-" + hour
    if key in weather:
        hourly_weather = weather[key]
    else:
        current = "0-" + str(datetime.datetime.now().hour + 2)
        hourly_weather = weather[current]

    rain = hourly_weather["precip"]
    temp = hourly_weather["temp"]
    return rain, temp


def data_and_direction(stop_num):
    return_data = []
    remove_chars = ["[", "]"]

    for item in StopSequencing.objects.all():
        if item.stop_num == stop_num:
            stop_data = item.stop_route_data
            stop_data = stop_data.split("], [")
            for character in remove_chars:
                for data in stop_data:
                    data = data.replace(character, "")
                    data = data.replace(", ", "_")
                    return_data.append(data)

    return return_data


def correcting_midnight(time):
    time_units = time.split(":")
    if int(time_units[0]) > 23:
        hour = int(time_units[0]) - 24
    else:
        hour = int(time_units[0])
    timestamp = leading_0_timestamp(str(hour), time_units[1], time_units[2])
    return timestamp


def ordering_predictions(list_size, predictions):
    output = [predictions[0]]
    for prediction in predictions:
        prediction = prediction.replace("]", "")
        if prediction not in output:
            temp_time = prediction.split("_")[-1]
            for item in range(len(output)):
                if prediction not in output:
                    check = output[item]
                    if temp_time < check.split("_")[-1]:
                        output.insert(item, prediction)
                    elif len(output) <= list_size and item == len(output) - 1:
                        output.append(prediction)
    return output


def return_departure_times(models):
    all_departure_times = {}
    for i in UniqueRoutes.objects.all():
        line_id = i.id
        for key, value in models.items():
            if key == line_id:
                destination = value[1]
                divisor = value[2]
                key_string = f"{line_id}_{destination}_{divisor}"
                all_departure_times[key_string] = [x.strip() for x in i.first_departure_schedule.split(',')]
    return all_departure_times


def return_models(routes):
    models = {}
    for i in routes:
        info = i.split("_")
        route = info[0]
        divisor = float(info[1])
        direction = info[2]
        destination = info[3]
        exists = os.path.isfile(f'./bus_routes/route_models/{direction}/RandForest_{route}.pkl')
        if exists:
            models[route + "_" + direction] = [pickle.load(open(f'.'
                                                                f'/bus_routes/route_models'
                                                                f'/{direction}/RandForest_{route}'
                                                                f'.pkl', "rb")), destination, divisor]
        else:
            pass
    return models


def return_arrival_times(all_arrival_times, hour, list_size, minute):
    # return dictionary of arrival times
    next_arrival_times = {}
    for i in all_arrival_times:
        next_times = []
        for j in all_arrival_times[i]:
            if len(next_times) < list_size:
                if len(j.split(':')[2]) == 2:
                    if int(hour) <= int(j.split(':')[0]):
                        if int(hour) == int(j.split(':')[0]) and int(minute) > int(j.split(':')[1]):
                            pass
                        else:
                            next_times.append(j)
                else:
                    next_times.append(j)

        next_arrival_times[i] = next_times
        return next_arrival_times


def return_journey_time_and_key(day, hour, key, month, rain, temp):
    route_info = key.split("_")
    route = str(route_info[0])
    direction = str(route_info[1])
    destination = str(route_info[2])
    new_key = route + "_" + direction + "_" + destination
    divisor = float(route_info[3])
    model = pickle.load(open(f'./bus_routes/route_models/{direction}/RandForest_{route}.pkl', "rb"))
    prediction = model.predict([[day, hour, month, rain, temp]])[0]
    predicted_journey_time = prediction / divisor
    return new_key, predicted_journey_time


def return_cut_off_and_predicted_times(hour, item, minute, predicted_journey_time):
    time_units = item.split(":")
    item = unit_to_seconds(time_units[0], time_units[1])
    predicted_time = float(item + predicted_journey_time)
    cut_off_time = (int(hour) * 3600) + (int(minute) * 60)
    return cut_off_time, predicted_time


def predictions_list(all_departure_times, day, hour, minute, month, rain, temp, predictions, today):
    # predict travel time for each routes departure to chosen stop
    for key, value in all_departure_times.items():
        new_key, predicted_journey_time = return_journey_time_and_key(day, hour, key, month, rain, temp)
        # assessment for times in the past, or if tomorrow
        for item in value:
            cut_off_time, predicted_time = return_cut_off_and_predicted_times(hour, item, minute,
                                                                              predicted_journey_time)
            if cut_off_time < predicted_time < 9000:
                print(cut_off_time)
                predicted_timestamp = seconds_to_timestamp(predicted_time)
                predicted_time = new_key + "_" + predicted_timestamp
                predictions.append(predicted_time)
            else:
                predicted_time = new_key + "_" + seconds_to_timestamp(predicted_time) + "(tomorrow)"
                predictions.append(predicted_time)
    return predictions
