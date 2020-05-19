# azscheduledevents
Scheduled Events is an Azure Metadata Service that gives your application time to prepare for virtual machine (VM) maintenance. It provides information about upcoming maintenance events (for example, reboot) so that your application can prepare for them and limit disruption. It's available for all Azure Virtual Machines types, including PaaS and IaaS on both Windows and Linux. <br /><br />
More information here: <br />
Linux VMs: https://docs.microsoft.com/en-us/azure/virtual-machines/linux/scheduled-events <br />
Windows VMs: https://docs.microsoft.com/en-us/azure/virtual-machines/windows/scheduled-events <br />

The files in the project can be used for a PoC to check on Scheduled Events and act on the same. The PoC can be used for both -- Azure VM and Azure VMSS.

## Project setup 
The current project set up I have is for Ubuntu Linux 18.04 <br> <br />

There are 4 files: <br />
**termnot.py:** This is a Python script which registers and later checks if there are any Scheduled Events for that VM or VMSS. <br /> 
**termnot.service:** The systemd service which executes the termnot.py script. <br />
**termnot.timer:** The systemd timer service which triggers the termnot.service repeatedly at an interval of 1 minute. <br />
**cloud-config:** Please ignore this file as of now. <br />

## More about termnot.py
1. **termnot.py** first registers and then checks if there are any Scheduled Events for that VM or for any instances of VMSS of which the VM instance may be a part of. This is done by using  **get_scheduled_events()**. **get_scheduled_events()** fetches the information by calling the **Scheduled Events API**<br />
2. Later, **handle_scheduled_events()** is called with the response received from **get_scheduled_events()**. This response has a list of all the VM instances (in a VMSS) or just a single VM instance (in case of a stand alone VM) for which the Scheduled Events are planned. The same found in the **Resources** property of the response. <br />
3. **handle_scheduled_events()** checks the instance metadata of the current VM instance (by calling the **Instance Metadata API** through the method **get_instance_metadata()**) to know what is the current instance name. This is done by checking the **compute.name** property in the response of **get_instance_metadata()**.
4. If the VM instance name (fetched from **get_instance_metadata()**) is actually present in the **Resources** property of the response (fetched from **get_scheduled_events()**) then the event handling logic is triggered. If the name is not present the code exits.
5. For the event handling logic, I am currently just creating a file, appending a text string with information on the Scheduled Event  and uploading it to a blob storage. This is done using the method **create_upload_blob()**. <br />
You can replace this by your own logic. <br />
6. For every event type in Scheduled Events, there is a wait time. If the event handling logic completes well before the wait time, then the event can be triggered (instead of waiting out for the entire wait time). This is done by calling the Scheduled Events API again and passing it the EventId. In **termnot.py**, the same is done through the **start_request()** method. <br />
7. The **start_request()** method should be invoked **only by one of the VM instances** whose name appears in the array of **Resources**. In this code, I am using the leader election logic as to - the **start_request()** method should be invoked by the VM instance whose name appears first in the **Resources** array (Refer point 2. of this section). <br />
<br />
Links referred for the source code snippets: <br />
https://docs.microsoft.com/en-us/azure/virtual-machines/linux/scheduled-events#python-sample <br />
https://docs.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-python#upload-blobs-to-a-container <br />


## How to use the source files
1. The file **termnot.py** should be copied to the desired location. The **create_upload_blob()** method should have the connection string of the Azure Storage account - this needs to be entered in the code. A container by the name **termnot** should be created in this storage account. <br />
2. The file **termnot.service** should have the full path of the file **termnot.service** in the **ExecStart** line. <br />
3. Both the files **termnot.service** and **termnot.timer** should be copied to **/etc/systemd/system** directory (for Ubuntu). <br />
4. Both **termnot.service** and **termnot.timer** should be enabled and started using the commands mentioned in cloud-config file which are as follows: <br />
 - systemctl enable termnot.service <br />
 - systemctl enable termnot.timer <br />
 - systemctl start termnot.service <br />
 - systemctl start termnot.timer <br />
 5. If the same set up needs to be replicted -- OR -- if the same set up has to be done for VMSS, then a **Managed Image** should be created of the VM which has the complete set up as mentioned above. The reference link for creation of images is: https://docs.microsoft.com/en-us/azure/virtual-machines/linux/capture-image 
