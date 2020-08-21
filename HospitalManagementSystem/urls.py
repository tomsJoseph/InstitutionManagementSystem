from django.urls import path
from . import views

urlpatterns = [
    path('selection_page_admin/', views.selection_page_admin, name='SelectPage4Admin'),

#  Common For All ==>[DONE]<==
   path('', views.department_home, name='DHome'),
    path('selection_page/', views.selection_page, name='SelectPage'),
    path('Inbox/', views.Inbox.as_view(), name='Inbox'),
    path('message/<int:pk>', views.Message.as_view(), name='Message'),
    path('new_message/', views.NewMessagePersonal.as_view(), name='NewMessage'),
    path('new_message_dept/', views.NewMessageDepartment.as_view(), name='NewMessageDepartment'),
    path('sentbox/', views.Sentbox.as_view(), name='Sentbox'),
    path('list_announcements/', views.ListAnnouncements.as_view(), name='ListAnnouncements'),
    path('announcement_single/<int:pk>', views.AnnouncementSingle.as_view(), name='AnnouncementSingle'),

#----------Department page--------------------
#  Any Department |==>[DONE]<==|
    path('Department/', views.department_home, name='DHome'),
    path('Department/<str:msg>', views.department_home, name='DHomeMsg'),
    path('inventory_list/', views.InventoryList.as_view(), name='InventoryList'),
    path('new_inventory/<str:red>', views.NewInventory.as_view(), name='NewInventory'),
    path('create_inventory_list/', views.InventoryCreate.as_view(), name='CreateInventoryList'),
    path('change_inventory_list/<int:pk>', views.ChangeInventory.as_view(), name='ChangeInventoryList'),
    path('purchase_list/', views.PurchasesList.as_view(), name='PurchaseList'),
    path('create_purchase_list/', views.Purchases.as_view(), name='CreatePurchaseList'),
    path('change_purchase_list/<int:pk>', views.ChangePurchaseItem.as_view(), name='ChangePurchaseList'),
    path('file_user_complaint/', views.FileUserComplaintFeedback.as_view(), name='FileUserComplaintFeedback'),
    path('register_attendance/', views.RegisterAttendance.as_view(), name='RegisterAttendance'),
    path('the_departed/', views.TheDeparted.as_view(), name='TheDeparted'),
    path('fatality_reports_list/', views.FatalityReportsList.as_view(), name='FatalityReportsList'),
    path('autopsy_list/', views.AutopsyList.as_view(), name='AutopsyList'),
    path('report_fatality/', views.ReportFatality.as_view(), name='ReportFatality'),
    path('report_fatality_unidentified/<str:unidentified>', views.ReportFatality.as_view(), name='ReportUnidentifiedFatality'),
    path('fatality_report/<int:pk>', views.FatalityReport.as_view(), name='FatalityReport'),
    path('write_fatality_report/<int:pk>', views.WriteFatalityReport.as_view(), name='WriteFatalityReport'),

#  Only the Medical departments |==>[DONE]<==|
    path('document_disease/', views.DocumentDisease.as_view(), name='DocumentDisease'),
    path('list_diseases/', views.DiseasesList.as_view(), name='DiseasesList'),
    path('change_document_disease/<int:pk>', views.UpdateDocumentDisease.as_view(), name='UpdateDocumentDisease'),
    path('create_causes/', views.CreateCause.as_view(), name='CreateCause'),
    path('create_causes/<int:redir>', views.CreateCause.as_view(), name='CreateCauseForDisease'),
    path('update_causes/<int:pk>', views.UpdateCause.as_view(), name='UpdateCause'),
    path('list_diseasecauses/', views.ListDiseaseCauses.as_view(), name='ListDiseaseCauses'),
    path('add_human_organs/', views.AddHumanOrgans.as_view(), name='AddHumanOrgans'),
    path('list_organs/', views.ListOrgans.as_view(), name='ListOrgans'),
    path('update_organ/<int:pk>', views.UpdateOrgan.as_view(), name='UpdateOrgan'),
    path('details_organ/<int:pk>', views.DetailsOrgan.as_view(), name='DetailsOrgan'),
    path('patients_que/', views.PatientsQue.as_view(), name='PatientsQue'),


#  OP and Casuality |==>[DONE]<==|
    path('patient_reception/', views.patient_reception, name='OPPage'),
    path('find_patient/', views.PatientSearchResultsView.as_view(), name='FindPatient'),
    path('patient_files/<int:pk>', views.PatientFiles.as_view(), name='UploadPatientFiles'),
    path('health_profile/<int:pk>', views.HealthProfile.as_view(), name='HealthProfile'),
    path('up_health_profile/<int:pk>', views.UpdateHealthRecord.as_view(), name='UpdateHealthRecord'),
    path('find_patient/find_records/<int:patient>/', views.HealthRecordSearchResultsView.as_view(), name='FindHealthRecords'),
    path('new_patient/<int:hr>', views.new_patient, name='NewPatient'),
    path('new_unknown_patient/', views.NewUnknownPatient.as_view(), name='NewUnknownPatient'),
    path('list_unknown_patients/', views.UnknownPatients.as_view(), name='UnknownPatients'),
    path('change_patient_details/<int:pk>', views.ChangePatientDetails.as_view(), name='ChangePatientDetails'),
    path('update_unknown_patients/<int:pk>', views.UpdateUnknownPatient.as_view(), name='UpdateUnknownPatient'),
    path('identify_unknown/<int:pk>', views.IdentifyUnknown.as_view(), name='IdentifyUnknown'),
    path('transfer_patient/<int:p_id>', views.TransferPatient.as_view(), name='TransferPatient'),
    path('edit_transfer_patient/<int:pk>', views.EditTransferPatient.as_view(), name='EditTransferPatient'),

#  Transport |==>[DONE]<==|
    path('whole_purchase_list/', views.TotalPurchaseList.as_view(), name='TotalPurchaseList'),
    path('enter_aquired_items/<int:pk>', views.EnterAquiredItems.as_view(), name='EnterAquiredItems'),
    path('old_purchase_list/', views.OldPurchaseList.as_view(), name='OldPurchaseList'),

#  Doctor,Pharmacy and Lab |==>[DONE]<==|
    path('find_patient_record/', views.search_record, name='SearchPage'),

#  Doctor  |==>[DONE]<==|
    path('discharge_patient/<int:p_id>', views.discharge, name='Discharge'),
    path('patient_consulting/<int:health_id>/', views.patientreview, name='PatientReview'),
    path('patient_report/<int:pk>', views.PatientReport.as_view(), name='PatientReport'),
    path('change_remark/<int:pk>', views.UpdateRemark.as_view(), name='ChangeHealthRemark'),
    path('change_test/<int:pk>', views.UpdateTest.as_view(), name='ChangeTest'),
    path('change_prescription/<int:pk>', views.UpdatePrescription.as_view(), name='ChangePrescription'),

#  Pharmacy |==>[DONE]<==|
    path('list_unknowns/', views.ListUnknowns.as_view(), name='ListUnknowns'),
    path('pharmacy/<int:pk>/', views.pharmacy, name='Pharmacy'),
    path('surgery_prepayment/<int:pk>', views.SurgeryPrepayment.as_view(), name='SurgeryPrepayment'),
    path('pay_bill/<int:pk>', views.BillPayment.as_view(), name='Payment'),
    path('document_medicine/', views.DocumentMedicine.as_view(), name='DocumentMedicine'),
    path('list_medicines/', views.MedicinesList.as_view(), name='MedicinesList'),
    path('change_document_medicine/<int:pk>', views.UpdateDocumentMedicine.as_view(), name='UpdateDocumentMedicine'),

#  Lab |==>[DONE]<==|
    path('tests_list/<int:pk>', views.TestList.as_view(), name='TestList'),
    path('take_test/<int:pk>', views.TakeTest.as_view(), name='TakeTest'),
    path('test_report/<int:pk>', views.TestReport.as_view(), name='TestReport'),
    path('test_history/<int:pk>', views.TestHistory.as_view(), name='TestHistory'),
    path('tests/', views.Tests.as_view(), name='Tests'),
    path('new_test/', views.NewTest.as_view(), name='NewTest'),
    path('edit_test/<int:pk>', views.EditTest.as_view(), name='EditTest'),

#  Surgeries |==>[DONE]<==|
    path('surgery_form/<int:pk>', views.InitiateSurgery.as_view(), name='SurgeryForm'),
    path('surgery_report_form/<int:pk>', views.WriteSurgeryReport.as_view(), name='WriteSurgeryReport'),
    path('surgery_report/<int:pk>', views.SurgeryReport.as_view(), name='SurgeryReport'),
    path('upload_surgery_docs/<int:pk>', views.UploadSurgeryDocs.as_view(), name='UploadSurgeryDocs'),
    path('surgery_list/', views.SurgeryList.as_view(), name='SurgeryList'),
    
# morgue
    path('morgue_list/', views.MorgueList.as_view(), name='MorgueList'),
    path('create_morgue/', views.CreateMorgue.as_view(), name='CreateMorgue'),
    path('edit_morgue/<int:pk>', views.EditMorgue.as_view(), name='EditMorgue'),

#  Room Service |==>[DONE]<==|
    path('list_room_types/', views.ListRoomTypes.as_view(), name='ListRoomTypes'),
    path('new_room_type/', views.NewRoomType.as_view(), name='NewRoomType'),
    path('edit_room_type/<int:pk>', views.EditRoomType.as_view(), name='EditRoomType'),
    path('list_rooms/', views.ListRooms.as_view(), name='ListRooms'),
    path('new_room/', views.NewRoom.as_view(), name='NewRoom'),
    path('edit_room/<int:pk>', views.RoomUpdate.as_view(), name='EditRoom'),
    path('patient_admission/<int:pk>', views.PatientAdmission.as_view(), name='PatientAdmission'),
    path('admission_details/<int:pk>', views.AdmissionDetails.as_view(), name='AdmissionDetails'),
    path('change_room/<int:pk>', views.ChangeRoom.as_view(), name='ChangeRoom'),
    path('list_admission', views.ListAdmissions.as_view(), name='PendingAdmission'),
    path('list_admission/<int:opt>', views.ListAdmissions.as_view(), name='AllAdmission'),

#----------Staff page--------------------
#  Common Staff
    path('Staff/', views.staff_home, name='SHome'),
    path('ChagePhoto/<int:pk>', views.ChangePhoto.as_view(), name='ChangeProfilePicture'),
    path('upload_certificate/', views.UploadCertificate.as_view(), name='UploadCertificates'),
    path('apply_leave', views.ApplyLeave.as_view(), name='ApplyLeave'),
    path('edit_leave_application/<int:pk>', views.EditLeaveApplication.as_view(), name='EditLeaveApplication'),
    path('file_staff_complaint/', views.FileStaffComplaintFeedback.as_view(), name='FileStaffComplaintFeedback'),
    path('update_personal_details/<int:pk>', views.UpdatePersonalDetails.as_view(), name='UpdatePersonalDetails'),
    path('change_password/', views.ChangePassword.as_view(), name='ChangePassword'),
    path('password_changed/', views.PasswordChanged.as_view(), name='PasswordChanged'),
    path('list_complaint/', views.ListComplaints.as_view(), name='ListComplaints'),
    path('change_complaint/<int:pk>', views.ChangeComplaint.as_view(), name='ChangeComplaint'),

#  Manager Staff
    path('register_new_staff/', views.signup, name='NewStaffRegistration'),
    path('make_announcement/', views.MakeAnnouncement.as_view(), name='MakeAnnouncement'),
    path('update_announcement/<int:pk>', views.UpdateAnnouncement.as_view(), name='UpdateAnnouncement'),
    path('list_leaves', views.ListLeaves.as_view(), name='ListLeaves'),
    path('manage_leaves/<int:pk>', views.ManageLeaves.as_view(), name='ManageLeaves'),
    path('staff_report/', views.ReportStaff.as_view(), name='ReportStaff'),
    path('staff_report/<int:pk>', views.ReportStaff.as_view(), name='ReportStaffSpecific'),
    path('list_staff_report/', views.StaffReportList.as_view(), name='StaffReportList'),
    path('edit_staff_report/<int:pk>', views.EditStaffReport.as_view(), name='EditStaffReport'),
    path('staff_attendance/', views.StaffAttendance.as_view(), name='StaffAttendance'),
    path('absentee_report/', views.AbsenteeReport.as_view(), name='AbsenteeReport'),
    path('detail_complaint/<int:pk>', views.ComplaintsInDetail.as_view(), name='ComplaintsInDetail'),
    path('all_staffs/', views.AllStaffs.as_view(), name='AllStaffs'),
    path('action_details/<int:pk>', views.ActionDetails.as_view(), name='ActionDetails'),
    path('change_shift_dep/<int:pk>', views.ChangeShiftDep.as_view(), name='ChangeShiftDep'),

    path('detailed_staff_report/<int:pk>', views.M_DetailStaffReport.as_view(), name='M_DetailStaffReport'),

 #  only for executive staff
    path('management/executive_home/', views.M_ExecutiveHome.as_view(), name='M_ExecutiveHome'),
    path('management/register_board_staff/', views.M_RegisterSuperintendent.as_view(), name='M_NewSuperintendRegistration'),

    path('management/m_salary_levels', views.M_SalaryManagement.as_view(), name='M_SalaryManagement'),
    path('management/m_change_basic_salary/<int:pk>', views.M_ChangeBasicSalary.as_view(), name='M_ChangeBasicSalary'),
    path('management/m_staff_of_level/<int:pk>', views.M_StaffOfLevel.as_view(), name='M_StaffOfLevel'),
    path('management/m_individual_salary/<int:pk>', views.M_IndividualSalary.as_view(), name='M_IndividualSalary'),
    path('management/m_change_individual_salary/<int:pk>', views.M_ChangeIndividualSalary.as_view(), name='M_ChangeIndividualSalary'),

    path('m_promo_or_depromo/<int:pk>', views.M_PromoOrDepromo.as_view(), name='M_PromoOrDepromo'),
    path('management/m_new_disciplinary_action/', views.M_NewDisciplinaryAction.as_view(), name='M_NewDisciplinaryAction'),
    path('management/m_all_disciplinary_actions/', views.M_AllDisciplinaryActions.as_view(), name='M_AllDisciplinaryActions'),
    path('management/m_edit_disciplinary_actions/<int:pk>/', views.M_ChangeDisciplinaryAction.as_view(), name='M_ChangeDisciplinaryAction'),

    path('management/m_departments', views.M_Departments.as_view(), name='M_Departments'),
    path('management/m_department_managers/<int:pk>', views.M_DepartmentManagers.as_view(), name='M_DepartmentManagers'),
    path('management/m_new_department_manager/<int:pk>', views.M_NewDepartmentManager.as_view(), name='M_NewDepartmentManager'),
    path('management/m_appoint_department_manager/<int:pk>', views.M_AppointDepartmentManager.as_view(), name='M_AppointDepartmentManager'),

    path('management/m_department_report/<int:pk>', views.M_DepartmentReport.as_view(), name='M_DepartmentReport'),
    path('management/inventory_report/<int:pk>', views.M_InventoryReport.as_view(), name='M_InventoryReport'),
    path('management/m_departmental_complaints/<int:pk>', views.M_DepartmentalComplaints.as_view(), name='M_DepartmentalComplaints'),
    path('management/m_staff_performances/<int:pk>', views.M_StaffPerformances.as_view(), name='M_StaffPerformances'),
    path('management/m_detail_staff_statistics/<int:pk>', views.M_DetailStaffStatistics.as_view(), name='M_DetailStaffStatistics'),
    path('management/m_staffs/<int:pk>', views.M_Staffs.as_view(), name='M_Staffs'),
    path('management/m_staff_reports/<int:pk>', views.M_StaffReports.as_view(), name='M_StaffReports'),
    path('management/m_personal_complaints/<int:pk>', views.M_PersonalComplaints.as_view(), name='M_PersonalComplaints'),
    path('management/m_department_statistics_list/', views.M_DepartmentStatsList.as_view(), name='M_DepartmentStatsList'),
    path('management/m_department_statistics/<int:pk>', views.M_DepartmentStatistics.as_view(), name='M_DepartmentStatistics'),
    path('management/m_lab_statistics', views.M_LabStatistics.as_view(), name='M_LabStatistics'),
    path('management/m_rooms_statistics', views.M_RoomsStatistics.as_view(), name='M_RoomsStatistics'),
    path('management/m_pharmacy_statistics', views.M_PharmacyStatistics.as_view(), name='M_PharmacyStatistics'),
    path('management/m_transport_statistics', views.M_TransportStatistics.as_view(), name='M_TransportStatistics'),
    path('management/m_diseases_statistics', views.M_DiseaseStatistics.as_view(), name='M_DiseaseStatistics'),
    path('management/m_morgue_statistics', views.M_MorgueStatistics.as_view(), name='M_MorgueStatistics'),
    path('management/m_staffs_unassigned/', views.M_StaffWithoutShift.as_view(), name='M_StaffWithoutShift'),

 #  only op manager
    path('shift_change', views.change_shift, name='ChangeShift'),

 #  manual
    path('manual/', views.Manual.as_view(), name='Manual'),
    ]
