import streamlit as st
import os
import time
from azure.ai.ml import MLClient, command
from azure.identity import DefaultAzureCredential
from azure.ai.ml.entities import Environment
from azure.core.exceptions import HttpResponseError

# Safely handle the import
try:
    from azure.core.exceptions import AzureError
except ImportError:
    AzureError = Exception

subscription_id = "d2bda5a8-0cf7-480c-bf1f-6d7ec7b665ba" 
resource_group = "PerceptBootcamp-aia-Norway" 
workspace_name = "percept-workspace"
compute_name = "Standard-D4s-v3-cluster-694450" #"Standard-DS3-v2-cluster-694450"  # D4s-v3-cpu694450 cpu not possible to use with command jobs, only clusters

# 1. Connect to Azure ML Workspace
ml_client = MLClient(DefaultAzureCredential(), 
                     subscription_id=subscription_id, 
                     rg=resource_group, 
                     workspace=workspace_name
                     )

#  Test the connection BEFORE trying to create the environment

# --- STEP 1: Variable Integrity Check ---
st.subheader("1. Environment Variable Check")
creds = {
    "SUB_ID": "d2bda5a8-0cf7-480c-bf1f-6d7ec7b665ba",
    "RG_NAME": "PerceptBootcamp-aia-Norway", # Ensure this is exactly what's in the Portal
    "WS_NAME": "percept-workspace"
}

for key, value in creds.items():
    if value is None or value == "None" or value == "":
        st.error(f"❌ {key} is missing or literal 'None'!")
    else:
        st.write(f"✅ {key} is set to: `{value}`")

# --- STEP 2: Client Hydration Check ---
st.subheader("2. SDK Client Validation")
try:
    ml_client = MLClient(
        credential=DefaultAzureCredential(),
        subscription_id=creds["SUB_ID"],
        resource_group_name=creds["RG_NAME"],
        workspace_name=creds["WS_NAME"]
    )
    
    # Force the SDK to reveal what it thinks the internal path is
    st.write(f"SDK internal RG: `{ml_client.resource_group_name}`")
    
    if ml_client.resource_group_name is None:
        st.error("🚨 CRITICAL: MLClient failed to ingest the Resource Group name!")
except Exception as e:
    st.error(f"Client Init Failed: {e}")

# --- STEP 3: The "Handshake" Test ---
st.subheader("3. Workspace & Identity Handshake")
try:
    # This triggers the actual API call to Azure
    ws_details = ml_client.workspaces.get(creds["WS_NAME"])
    st.success(f"🎉 Success! Connected to Workspace ID: `{ws_details.id}`")
    
except HttpResponseError as e:
    st.error("### 🛑 Authorization / Scope Failure")
    st.code(f"Error Code: {e.error.code if e.error else 'Unknown'}")
    st.code(f"Message: {e.message}")
    
    # Logic to decode the 'None' error
    if "resourceGroups/None" in e.message:
        st.warning("👉 **THE PROBLEM:** The SDK is sending 'None' as the Resource Group name. "
                   "This usually means the variable passed to MLClient was null at initialization.")
    elif "AuthorizationFailed" in e.message:
        st.warning("👉 **THE PROBLEM:** The Managed Identity is recognized, but it doesn't have 'Reader' or 'Contributor' "
                   "access to the Workspace. Go to IAM in Azure Portal to fix this.")
    

st.title("ML Control Center")
hidden_nodes = st.slider("Number of neurons (hidden nodes)", 1, 5)

# 1. Get the absolute path of the directory where your Web App code lives
# In Azure Web Apps, this is usually /home/site/wwwroot
base_dir = os.path.abspath(os.path.dirname(__file__))
code_dir = os.path.join(base_dir, "src")
# 1. Point to your local env.yml (the one we rewrote for Python 3.8/TF 2.13)
# Assuming it's in your /src folder
conda_file_path = os.path.join(code_dir, "environment.yml")

# Use the environment variable Azure sets for the root of the site DID NOT WORK
#site_root = os.environ.get("HOME", "/home") + "/site/wwwroot"
#code_dir = os.path.join(site_root, "src")


if not os.path.exists(code_dir):
    # Fallback for local testing
    code_dir = os.path.abspath("./src")

st.write(f"Uploading code from: {code_dir}")
st.write(f"Code_dir content: {os.listdir(code_dir)}")
if st.button("Start Training Job"):
 
     # 2. Define the Environment object
    st.write(f"Creating environment using: {conda_file_path}")
    custom_env = Environment(
        
        name="lstm_training_env",
        description="Custom environment for LSTM training",
        # Use a reliable base image that always exists
        image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04:latest",
        conda_file=conda_file_path,
    )
    ################### update to fix relative path issues
    # 2. Register the Environment (if not already done)
    st.info("Registering environment...")
    registered_env = ml_client.environments.create_or_update(custom_env)
    
    job = command(

        # Use a plain string for the path, ensuring no 'azureml:' prefix is added manually
        code="./src",
        command="python3 train_lstm.py --hidden_nodes ${{inputs.hidden_nodes}}",
        inputs={"hidden_nodes": hidden_nodes},
        # Use the ID of the registered environment
        environment=registered_env.id, 
        compute=compute_name,
        experiment_name="lstm-training-webapp",
        display_name="LSTM_Final_Run"
    )
    ####################
    """ 
    job = command(
        name=f"lstm-train-{int(time.time())}", # Add a unique name
        code=code_dir, 
        inputs={"hidden_nodes": hidden_nodes},
        command="python3 train_lstm.py --hidden_nodes 5", # ${{inputs.hidden_nodes}}",
        environment=custom_env, # "AzureML-sklearn-1.0-ubuntu20.04-py38-cpu@latest",
        compute=compute_name
    )"""
    ##### TEMPORARY code
    from azure.ai.ml.entities import Environment, BuildContext

    # 1. Define Environment with an explicit name

    # 2. Register it FIRST
    st.info("Registering environment...")
    ml_client.environments.create_or_update(custom_env)

    # 3. Submit the job using the string name of the registered environment
    job = command(
        code="/tmp/8de84fcf8927f7a/pages/src",
        command="python3 train_lstm.py --hidden_nodes ${{inputs.hidden_nodes}}",
        inputs={"hidden_nodes": 1},
        environment=f"{custom_env}:1", # Use the versioned string
        compute=compute_name, #"Standard-D4s-v3-cluster-694450",
        experiment_name="lstm-training-webapp"
    )

    st.info("Submitting job...")
    returned_job = ml_client.jobs.create_or_update(job)
    st.success(f"Job submitted: {returned_job.name}")

    ##### END TEMPORARY CODE
    
    try:
        st.info(f"Submitting job from: {code_dir}")
        st.write("Checking job attributes before submission...")
        # This line will tell us if any attribute is missing before we even send it
        st.json(job._to_dict())
        returned_job = ml_client.jobs.create_or_update(job)
        st.success(f"Job created! ID: {returned_job.name}")

    except Exception as e:
        st.error(f"### Job Submission Failed")
        
        # This is the most reliable way to show the error message in Python 3.12
        error_msg = str(e)
        st.code(error_msg)
        
        # Logical check for common issues
        if "AssetException" in error_msg or "upload" in error_msg.lower():
            st.warning("⚠️ **Diagnosis:** The SDK is failing to zip or upload the 'src' folder.")
            st.info("This usually happens because the Web App identity lacks 'Storage Blob Data Contributor' "
                    "permissions on the workspace storage account.")
            


