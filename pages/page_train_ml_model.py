import streamlit as st
import os
import time
from azure.ai.ml import MLClient, command
from azure.identity import DefaultAzureCredential
from azure.ai.ml.entities import Environment
from azure.ai.ml import Code
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

    # 1. Register the Environment separately
    # This creates the versioned asset in Azure ML Studio
    try:
        st.info("Registering Environment asset...")
        # This call converts your object into a real Azure resource
        registered_env = ml_client.environments.create_or_update(custom_env)
        # We only want the ID (the long string starting with /subscriptions/...)
        env_id = registered_env.id 
    except Exception as e:
        st.error(f"Environment registration failed: {e}")
        st.stop()

    # 2. Define the local path clearly
    # Verify this path exists in your Streamlit environment
    local_src_path = "/tmp/8de88dedfddf46b/pages/src"

    if not os.path.exists(local_src_path):
        st.error(f"🚨 Path does not exist: {local_src_path}")
        st.stop()

    # 3. Manually register the code asset
    # This forces the SDK to upload the folder to Azure Storage immediately
    try:
        st.info("Uploading source code to Azure Storage...")
        my_code = Code(path=local_src_path)
        uploaded_code = ml_client.code.create_or_update(my_code)
        
        # We now have a clean Azure Resource ID (it starts with /subscriptions/...)
        code_id = uploaded_code.id
        st.success("✅ Code uploaded successfully.")
    except Exception as e:
        st.error(f"Failed to upload code: {e}")
        st.stop()
        # 3. Submit the Job using ONLY the ID strings
    job = command(
        code=code_id,  # <--- Use the ID from the upload above
        command="python train_lstm.py --hidden_nodes ${{inputs.hidden_nodes}}",
        inputs={"hidden_nodes": 1},
        environment=env_id, # Use the registered_env.id from our previous step
        compute="Standard-D4s-v3-cluster-694450",
        experiment_name="lstm-training-webapp"
    )
    # 3. Build the Job using STRINGS, not objects
    """job = command(
        code=local_code_path, # Pure string path
        command="python train_lstm.py --hidden_nodes ${{inputs.hidden_nodes}}",
        inputs={"hidden_nodes": 1},
        environment=env_id,   # Using the ID string from Step 1
        compute="Standard-D4s-v3-cluster-694450",
        experiment_name="lstm-training-webapp"
    )"""

    # 4. Final Submission
    try:
        st.info("Submitting Job...")
        returned_job = ml_client.jobs.create_or_update(job)
        st.success(f"🚀 Job submitted! Status: {returned_job.status}")
        st.link_button("View in Azure Studio", returned_job.studio_url)
    except Exception as e:
        st.error("Submission failed. Check the error below:")
        st.code(str(e))
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
            


