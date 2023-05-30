import pythoncom
import win32com.client
import datetime

NAME = "Focus Time App Trigger"

scheduler = win32com.client.Dispatch('{6bff4732-81ec-4ffb-ae67-b6c1bc29631f}', clsctx=pythoncom.CLSCTX_LOCAL_SERVER)
scheduler = win32com.client.Dispatch('Schedule.Service')
scheduler.Connect()
task_folder = scheduler.GetFolder('\\')
# test = task_folder.GetTask("aa")
# task_folder.DeleteTask('Test Task', 0)
# triggers = list(test.Definition.Triggers)
# tasks = task_folder.GetTasks(0)
# for task in tasks:
#     if task.Name == NAME:
#         pass

task_def = scheduler.NewTask(0)

# Defining the Start time of job
start_time = datetime.datetime.now() + datetime.timedelta(minutes=1)

# For Daily Trigger set this variable to 2 ; for One time run set this value as 1
TASK_TRIGGER_DAILY = 2
trigger = task_def.Triggers.Create(TASK_TRIGGER_DAILY)

trigger.Repetition.Interval = "PT1M"  # repeat every 1 minute
trigger.StartBoundary = start_time.isoformat()

# Create action
TASK_ACTION_EXEC = 0
action = task_def.Actions.Create(TASK_ACTION_EXEC)
action.ID = 'Trigger sync'
action.Path = 'D:\\temp\\directory-checksum.exe'
action.Arguments = '-max-depth 1 D:/temp/aichat'

# Set parameters
task_def.RegistrationInfo.Description = 'Triggers the Focus Time App synchronization mechanism'
task_def.Settings.Enabled = True
task_def.Settings.StopIfGoingOnBatteries = False

# Register task
# If task already exists, it will be updated
TASK_CREATE_OR_UPDATE = 6
TASK_LOGON_NONE = 0
task_folder.RegisterTaskDefinition(
    'Test Task',  # Task name
    task_def,
    TASK_CREATE_OR_UPDATE,
    '',  # No user
    '',  # No password
    TASK_LOGON_NONE
)
