from django.db import transaction
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import render

# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
import json

from tickets.models import Screen


def process_seats(seat_info):
    '''
    Creates proper seating dictionary of rows with True for unoccupied seat
    :param seat_info:
    :return:
    '''
    seats = {}
    for row in seat_info:
        number_of_seats = seat_info[row]['numberOfSeats']
        aisle_seats = seat_info[row]['aisleSeats']
        temp = []
        aisle_begin = True
        for i in range(number_of_seats):
            if i in aisle_seats:
                if aisle_begin:
                    temp.append(None)
                    aisle_begin = False
                else:
                    aisle_begin = True
            temp.append([i, True])
        last_aisle_seat = max(aisle_seats)
        last_aisle_seat_index = temp.index([last_aisle_seat, True])
        temp.insert(last_aisle_seat_index + 1, None)  # insert None to capture aisle property of last seat
        seats[row] = temp
    return seats


@csrf_exempt
def screens(request):
    '''
    Screen/Theatre save and fetch
    :param request:
    :return:
    '''
    if request.method == 'GET':
        """
        :return: list of screens
        """
        try:
            res, status = Screen.list_screen(), 200
            return JsonResponse(res, safe=False, status=status)
        except Exception as e:
            return JsonResponse({'Error': str(e)})
    elif request.method == 'POST':
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                name = data['name']
                seat_info = data['seatInfo']
                s = Screen.objects.filter(name=name)
                if s:
                    s.seats = process_seats(seat_info)
                    s.update()
                    return JsonResponse('Screen data updated successfully', safe=False, status=200)
                else:
                    s = Screen()
                    s.name = name
                    s.seats = process_seats(seat_info)
                    s.save()
                    return JsonResponse('Screen data saved successfully', safe=False, status=200)
            except Exception as e:
                return JsonResponse('Invalid payload' + str(e), safe=False, status=400)
        else:
            return JsonResponse('Invalid content type', safe=False, status=400)
    elif request.method == 'DELETE':
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                name = data['name']
                s = Screen.objects.filter(name=name)
                if s:
                    s.delete()
                    return JsonResponse('Screen data deleted successfully', safe=False, status=202)
                else:
                    return JsonResponse('Screen not found', safe=False, status=402)
            except Exception as e:
                return JsonResponse('Invalid payload', safe=False, status=400)
        else:
            return JsonResponse('Invalid content type', safe=False, status=400)
    else:
        return HttpResponseNotAllowed(request)


@csrf_exempt
@transaction.atomic
def booking(request, screen_name):
    '''
    Reserve seat and update db
    :param request:
    :param screen_name:
    :return:
    '''
    if request.method == 'POST':
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                booking_seats = data['seats']
                s = Screen.objects.filter(name=screen_name)
                if s:
                    seats = s[0].seats
                    try:
                        for row in booking_seats:
                            for seat in booking_seats[row]:
                                current_seat_index = seats[row].index([seat, True])
                                seats[row][current_seat_index][1] = False
                        s.update(seats=seats)
                        return JsonResponse('Seats reserved successfully', safe=False, status=200)
                    except Exception as e:
                        return JsonResponse('Seats unavailable', safe=False, status=400)
                else:
                    return JsonResponse('Screen not found', safe=False, status=400)
            except Exception as e:
                return JsonResponse('Invalid payload' + str(e), safe=False, status=400)
        else:
            return JsonResponse('Invalid content type', safe=False, status=400)
    else:
        return HttpResponseNotAllowed(request)


def seats(request, screen_name):
    '''
    Fetch seats information from db
    :param request:
    :param screen_name:
    :return:
    '''
    if request.method == 'GET':
        try:
            status = request.GET.get('status')
            num_seats = request.GET.get('numSeats')
            choice = request.GET.get('choice')
            if num_seats and choice:
                s = Screen.objects.filter(name=screen_name)
                if s:
                    s = s[0]
                    seats = s.seats
                    try:
                        required_row = choice[0]
                        required_seat = int(choice[1:])
                        row = seats[required_row]
                        numSeats = int(num_seats)
                        first_potential_seat = required_seat - numSeats + 1
                        first_potential_seat = max(first_potential_seat, 0)
                        availableSeats = []
                        result_found = False
                        for i in range(first_potential_seat, required_seat):
                            if [i, True] in row:
                                starting_index = row.index([i, True])
                                for seat in row[starting_index:numSeats + starting_index]:
                                    if seat and seat in row:
                                        availableSeats.append(seat[0])
                                    else:
                                        availableSeats = []
                                        break
                            else:
                                continue
                            if len(availableSeats) == numSeats:
                                result_found = True
                                break
                        if result_found:
                            response = {'availableSeats': {required_row: availableSeats}}
                            return JsonResponse(response, safe=False, status=200)
                        else:
                            return JsonResponse('Seats unavailable', safe=False, status=400)
                    except Exception as e:
                        return JsonResponse('Seats unavailable', safe=False, status=400)
                else:
                    return JsonResponse('Screen not found', safe=False, status=400)
            elif status == 'unreserved':
                s = Screen.objects.filter(name=screen_name)
                if s:
                    s = s[0]
                    seats = s.seats
                    response = {'seats': {}}
                    try:
                        for row in seats:
                            response['seats'][row] = []
                            for seat in seats[row]:
                                if seat and seat[1]:
                                    response['seats'][row].append(seat[0])
                        return JsonResponse(response, safe=False, status=200)
                    except Exception as e:
                        return JsonResponse('Seats unavailable', safe=False, status=400)
                else:
                    return JsonResponse('Screen not found', safe=False, status=400)
            else:
                return JsonResponse('Invalid payload', safe=False, status=400)
        except Exception as e:
            return JsonResponse('Invalid payload' + str(e), safe=False, status=400)
    else:
        return HttpResponseNotAllowed(request)


@csrf_exempt
def screen(request, screen_name):
    if request.method == 'GET':
        print(screen_name)
        if screen_name:
            try:
                return JsonResponse({'screen': screen_name, 'msg': 'screen found successfully.'}, status=200)
            except Exception as e:
                return JsonResponse({'Error': str(e)})
        else:
            return JsonResponse('Invalid request type', safe=False, status=400)
    else:
        return HttpResponseNotAllowed(request)
