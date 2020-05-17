#!/usr/bin/python

import json
import socket
import urllib2
import os, uuid
import time
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

se_metadata_url = "http://169.254.169.254/metadata/scheduledevents?api-version=2019-01-01"
instance_metadata_url = "http://169.254.169.254/metadata/instance?api-version=2017-08-01"

def get_instance_metadata():
    print("get_instance_metadata")
    req = urllib2.Request(instance_metadata_url)
    req.add_header('Metadata', 'true')
    resp = urllib2.urlopen(req)
    data = json.loads(resp.read())
    return data


def get_scheduled_events():
    print("get_scheduled_events")
    req = urllib2.Request(se_metadata_url)
    req.add_header('Metadata', 'true')
    resp = urllib2.urlopen(req)
    data = json.loads(resp.read())
    return data


def create_upload_blob(str_print):
    connect_str = "intsProtocol=https;AccountName=termnotstoracc;AccountKey=4QiT8y12e3igm7ehFyLlrQKrxhI1zA3CdcWycCVdLKF9BLoOVRDVyOxjm0pPw+pNulVR5m/0q8wc5lse2eqKog==;EndpointSuffix=core.windows.net"
    container_name = "termnot"
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    # Create a file in local data directory to upload and download
    local_path = "./"
    local_file_name = "quickstart" + str(uuid.uuid4()) + ".txt"
    upload_file_path = os.path.join(local_path, local_file_name)

    # Write text to the file
    file = open(upload_file_path, 'w')
    file.write(str_print)
    file.close()

    # Create a blob client using the local file name as the name for the blob
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=local_file_name)

    print("\nUploading to Azure Storage as blob:\n\t" + local_file_name)

    # Upload the created file
    with open(upload_file_path, "rb") as data:
        blob_client.upload_blob(data)

    return


def start_request(eventId):
    reqdata = {
               "StartRequests": [{
               "EventId": eventId
                    }]
                    }
    req = urllib2.Request(se_metadata_url, json.dumps(reqdata))
    req.add_header('Metadata', 'true')
    resp = urllib2.urlopen(req)
 
    return resp



def handle_scheduled_events(data):
    print("handle_scheduled_events")
    vm_metadata = get_instance_metadata()
    this_host = vm_metadata['compute']['name']
    for evt in data['Events']:
        eventid = evt['EventId']
        status = evt['EventStatus']
        resources = evt['Resources']
        eventtype = evt['EventType']
        resourcetype = evt['ResourceType']
        notbefore = evt['NotBefore'].replace(" ", "_")

        #Perform the logic of handling events only if the VM instance name appears in the list of Resources
        if this_host in resources:
            str_print = "+ Scheduled Event. This host " + this_host +" is scheduled for " + eventtype + " not before " + notbefore
            print(str_print)

            #Logic for handling events begins here ---
            #In my case I am creating a file with the details of the events and uploading it to the blob
            create_upload_blob(str_print) 
            #Logic for handling events ends here ---

            #Leader election -- the request to start the event should only be sent by one of the instances.
            #Over here we elect the leader whose name appears first in the list.
            #We wait for a pre-decided time of 30 secs and then initiate the request to start the event
            this_host_index = resources.index(this_host)
            print("******")
            print(this_host_index)
            print("*****")

            if this_host_index == 0:
                time.sleep(30)
            #Start the request
                resp = start_request(evt['EventId']) 
            return 




def main():
    #Fetch the scheduled events
    data = get_scheduled_events()
    print(data)

    #Handle the scheduled events
    schedEventsResp = handle_scheduled_events(data)
    print("Done!!!")


if __name__ == '__main__':
    main()

