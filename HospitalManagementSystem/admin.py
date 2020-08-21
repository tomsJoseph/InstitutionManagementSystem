from django.contrib import admin
from django.contrib.admin import AdminSite
from django.http import HttpResponse
from .models import Shift, Country, State, District, Level, Hospital, Department, Announcement, Attendance, Qualification, Fee, Gender, Accident
from django.shortcuts import get_object_or_404, render, redirect
from datetime import time

admin.site.register(Accident)
admin.site.register(Country)
admin.site.register(State)
admin.site.register(District)
admin.site.register(Fee)
admin.site.register(Level)
admin.site.register(Hospital)
admin.site.register(Department)
admin.site.register(Qualification)
admin.site.register(Gender)

admin.site.site_url = "/Hospital"

'''
for automatic shifting to work all shifts should have
all kinds of neccessary personal like doctors,nurses etc.
if not use manual shifting.
'''
def Initialize_shifts(modeladmin, request, queryset):
    def set_shift(staffs, key):
        shift = Shift.objects.get(shift_name = key)
        for staff in staffs:
            staff.shift = shift
            staff.save()

    departments = Department.objects.all()
    levels = Level.objects.all()

    for dep in departments:
        if dep.is_medical:
            for lev in levels:
                staffs = dep.appuser_set.filter(pro_level = lev)
                cou = staffs.count()/3

                staff_set = staffs[:cou]
                set_shift(staff_set, 'A')
                staff_set = staffs[cou:(2*cou)]
                set_shift(staff_set, 'B')
                staff_set = staffs[(2*cou):(3*cou)]
                set_shift(staff_set, 'C')
        else:
            staffs = dep.appuser_set.all()
            cou = staffs.count()/3

            staff_set = staffs[:cou]
            set_shift(staff_set, 'A')
            staff_set = staffs[cou:(2*cou)]
            set_shift(staff_set, 'B')
            staff_set = staffs[(2*cou):(3*cou)]
            set_shift(staff_set, 'C')

        Shift.predict_shift_change()


def reset_shifts(modeladmin, request, queryset):
    Shift.objects.filter(shift_name = 'A').update(start_time = time(0), end_time = time(8))
    Shift.objects.filter(shift_name = 'B').update(start_time = time(8), end_time = time(16))
    Shift.objects.filter(shift_name = 'C').update(start_time = time(16), end_time = time(0))
    Shift.predict_shift_change()
    

def change_shift(modeladmin, request, queryset):
    shifts = Shift.objects.all()
    sh = shifts.get(end_time = time(16))
    sh.end_time = time(5)
    sh.save()

    sh = shifts.get(end_time = time(0))
    sh.end_time = time(16)
    sh.start_time = time(8)
    sh.save()

    sh = shifts.get(end_time = time(8))
    sh.end_time = time(24)
    sh.start_time = time(16)
    sh.save()

    sh = shifts.get(end_time = time(5))
    sh.end_time = time(8)
    sh.start_time = time(0)
    sh.save()

    Shift.predict_shift_change()


class ShiftAdmin(admin.ModelAdmin):
    actions = [Initialize_shifts, reset_shifts, change_shift]

admin.site.register(Shift, ShiftAdmin)
