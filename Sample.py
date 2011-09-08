#!/usr/bin/env python
# encoding: utf-8
# 

from bottle import route, run, request, redirect

import bottle
bottle.debug(True)

import cgi
import os
import datetime
import logging
import urllib

from xml.dom import minidom
from scormcloud.client import ScormCloudService
from scormcloud.client import ScormCloudUtilities


appId =  ""    # e.g."3ABCDJHRT"
secretKey = ""    # e.g."aBCDEF7o8AOF7qsP0649KfLyXOlfgyxyyt7ecd2U"
serviceUrl = "http://cloud.scorm.com/EngineWebServices"
origin = ScormCloudUtilities.get_canonical_origin_string('your company', 
         'sample application', '1.0')
cloud = ScormCloudService.withargs(appId, secretKey, serviceUrl, origin)

sampleBaseUri = "http://localhost:8080"

@route('/')
@route('/sample')
def Sample():
	html = """
	<h1>SCORM Cloud Sample - Python</h1>
	
	<p>This sample is intended as an example for how to use the different SCORM Cloud web services available for use.</p>
	
	<h3><a href="/sample/courselist">Course List</a></h3>
	"""
	dsvc = cloud.get_debug_service()
	if dsvc.ping():
		html += "<p style='color:green'>CloudPing call was successful.</p>"
	else:
		html += "<p style='color:red'>CloudPing call was not successful.</p>"
	if dsvc.authping():
		html += "<p style='color:green'>CloudAuthPing call was successful.</p>"
	else:
		html += "<p style='color:red'>CloudAuthPing call was not successful.</p>"

	return html

@route('/sample/courselist')
def CourseList():
	html = """
	<style>td {padding:3px 10px 3px 0;} </style>
	<h1>Course List</h1>
	"""
	upsvc = cloud.get_upload_service()
						
	importurl = sampleBaseUri + "/sample/importcourse"
	cloudUploadLink = upsvc.get_upload_url(importurl)
	
	html += "<h3>Import a new course</h3>"
	html += '<form action="' + cloudUploadLink + '" method="post" enctype="multipart/form-data">'
	html += """<h4>Select Your Zip Package</h4>
		<input type="file" name="filedata" size="40" />
		<input type="submit" value="Import This Course"/>
	</form>
	"""
	csvc = cloud.get_course_service()
	courses = csvc.get_course_list()
	
	coursecount = courses is not None and len(courses) or 0
	html += "<p>Your SCORM Cloud realm contains " + str(coursecount) + " courses associated with your appId.</p>"
	
	rsvc = cloud.get_registration_service()
	regs = rsvc.get_registration_list()
		
	allcourses = []
	if coursecount > 0:
		html += """<table>
		<tr><td>Title</td><td>Registrations</td><td></td><td></td></tr>

		"""
		def regFilter(x): return x.courseId == courseData.courseId
		
		for courseData in courses:
			
			courseRegs = filter(regFilter,regs)
			
			html += "<tr><td>" + courseData.title + "</td>"
			html += '<td><a href="/sample/course/regs/' + courseData.courseId + '">' + str(len(courseRegs)) + '</a></td>'
			html += '<td><a href="/sample/course/properties/' + courseData.courseId + '">Properties Editor</a></td>'
			html += '<td><a href="/sample/course/preview/' + courseData.courseId + '?redirecturl=' + sampleBaseUri + '/sample/courselist">Preview</a></td>'
			html += '<td><a href="/sample/course/delete/' + courseData.courseId + '">Delete</a></td></tr>'
		html += "</table>"
	
	repsvc = cloud.get_reporting_service()
	repAuth = repsvc.get_reportage_auth("freenav",True)
	repUrl = repsvc.get_reportage_url(repAuth)

	html += "<h3><a href='" + repUrl + "'>Go to reportage for your App Id.</a></h3>"
	return html

@route('/sample/course/properties/:courseid')
def Properties(courseid):

	csvc = cloud.get_course_service()
	propsUrl = csvc.get_property_editor_url(courseid)
	
	html = """
	<h1>Properties Editor</h1>
	<p><a href="/sample/courselist">Return to Course List</a></p>
	"""
	
	html += "<iframe width='800px' height='500px' src='" + propsUrl + "'></iframe>"
	
	html += "<h2>Edit course attributes directly:</h2>"
	html += "<form action='/sample/course/attributes/update/" + courseid + "' method='Get'>"
	
	html += "Attribute:<select name='att''>"
	attributes = csvc.get_attributes(courseid)
	for (key, value) in attributes.iteritems():
		if value == 'true' or value == 'false':
			html += "<option value='" + key + "'>" + key + "</option>"
	
	html += """
	</select>
	<select name="attval">
		<option value=""></option>
		<option value="true">true</option>
		<option value="false">false</option>
	</select>
	<input type="hidden" name="courseid" value="<?php echo $courseId; ?>"/>
	<input type="submit" value="submit"/>
</form>
	
	"""
	
	return html

@route('/sample/course/attributes/update/:courseid')
def UpdateAttribute(courseid):
	csvc = cloud.get_course_service()
	
	atts = {}
	atts[request.GET.get('att')] = request.GET.get('attval')
	
	data = csvc.update_attributes(courseid,None,atts)
	
	propsUrl = "/sample/course/properties/" + courseid
	redirect(propsUrl)


@route('/sample/course/preview/:courseid')
def Preview(courseid):

	redirectUrl = request.GET.get('redirecturl')
	csvc = cloud.get_course_service()
	previewUrl = csvc.get_preview_url(courseid,redirectUrl)
	
	redirect(previewUrl)
	
@route('/sample/course/delete/:courseid')
def Delete(courseid):

	csvc = cloud.get_course_service()
	response = csvc.delete_course(courseid)

	redirectUrl = 'sample/courselist'
	redirect(redirectUrl)

	
@route('/sample/importcourse')
def ImportCourse():
	location = request.GET.get('location')
	csvc = cloud.get_course_service()
	importResult = csvc.import_uploaded_course(None,location)
	
	upsvc = cloud.get_upload_service()
	resp = upsvc.delete_file(location)
	
	redirectUrl = 'sample/courselist'
	redirect(redirectUrl)
	
@route('/sample/course/regs/:courseid')
def CourseRegs(courseid):
	
	html = """
	<style>td {padding:3px 10px 3px 0;} </style>
	<h1>Registrations</h1>
	<p><a href="/sample/courselist">Return to Course List</a></p>
	"""
	html += """<table>
	<tr><td>RegId</td><td>Completion</td><td>Success</td><td>Time(s)</td><td>Score</td><td></td><td></td></tr>

	"""
	
	rsvc = cloud.get_registration_service()
	regs = rsvc.get_registration_list(None,courseid)
	for reg in regs:
		xmldoc = rsvc.get_registration_result(reg.registrationId, "course")
		regReport = xmldoc.getElementsByTagName("registrationreport")[0]
		regid = regReport.attributes['regid'].value
		
		launchUrl = rsvc.get_launch_url(regid, sampleBaseUri + "/sample/course/regs/" + courseid)
		
		html += "<tr><td>" + regid + "</td>"
		html += '<td>' + regReport.getElementsByTagName("complete")[0].childNodes[0].nodeValue + '</td>'
		html += '<td>' + regReport.getElementsByTagName("success")[0].childNodes[0].nodeValue + '</td>'
		html += '<td>' + regReport.getElementsByTagName("totaltime")[0].childNodes[0].nodeValue + '</td>'
		html += '<td>' + regReport.getElementsByTagName("score")[0].childNodes[0].nodeValue + '</td>'
		html += '<td><a href="' + launchUrl + '">Launch</a></td>'
		html += '<td><a href="/sample/reg/reset/' + regid + '?courseid=' + courseid + '">reset</a></td>'
		html += '<td><a href="/sample/reg/resetglobals/' + regid + '?courseid=' + courseid + '">reset globals</a></td>'
		html += '<td><a href="/sample/reg/delete/' + regid + '?courseid=' + courseid + '">Delete</a></td></tr>'
	html += "</table>"
	
	repsvc = cloud.get_reporting_service()
	repAuth = repsvc.get_reportage_auth("freenav",True)
        repUrl = repsvc.get_course_reportage_url(repAuth, courseid)
	
	html += "<h3><a href='" + repUrl + "'>Go to reportage for your course.</a></h3>"
	
	return html

@route('/sample/reg/delete/:regid')
def DeleteReg(regid):

	rsvc = cloud.get_registration_service()
	response = rsvc.delete_registration(regid)

	redirectUrl = '/sample/course/regs/' + request.GET.get('courseid')
	redirect(redirectUrl)
	
@route('/sample/reg/reset/:regid')
def ResetReg(regid):

	rsvc = cloud.get_registration_service()
	response = rsvc.reset_registration(regid)

	redirectUrl = '/sample/course/regs/' + request.GET.get('courseid')
	redirect(redirectUrl)
	
@route('/sample/reg/resetglobals/:regid')
def ResetGlobals(regid):

	rsvc = cloud.get_registration_service()
	response = rsvc.reset_global_objectives(regid)
	
	redirectUrl = '/sample/course/regs/' + request.GET.get('courseid')
	redirect(redirectUrl)
	
	
run(host='localhost',port=8080,reloader=True)
