import streamlit as st
import os
import time
from azure.ai.ml import MLClient, command
from azure.identity import DefaultAzureCredential
# Safely handle the import
try:
    from azure.ai.ml.exceptions import AssetException
except ImportError:
    AssetException = Exception



subscription_id= "d2bda5a8-0cf7-480c-bf1f-6d7ec7b665ba"
resource_group = "PerceptBootcamp-aia-Norway"
workspace_name = "percept-workspace"
compute="D4s-v3-cpu694450"

# 1. Connect to Azure ML Workspace
ml_client = MLClient(DefaultAzureCredential(), 
                     subscription_id=subscription_id, 
                     rg=resource_group, 
                     workspace=workspace_name
                     )

st.title("ML Control Center")
hidden_nodes = st.slider("Number of neurons (hidden nodes)", 1, 5)

# 1. Get the absolute path of the directory where your Web App code lives
# In Azure Web Apps, this is usually /home/site/wwwroot
base_dir = os.path.abspath(os.path.dirname(__file__))
code_dir = os.path.join(base_dir, "src")

# Use the environment variable Azure sets for the root of the site DID NOT WORK
#site_root = os.environ.get("HOME", "/home") + "/site/wwwroot"
#code_dir = os.path.join(site_root, "src")

if not os.path.exists(code_dir):
    # Fallback for local testing
    code_dir = os.path.abspath("./src")

st.write(f"Uploading code from: {code_dir}")
st.write(f"Code_dir content: {os.listdir(code_dir)}")
if st.button("Start Training Job"):
    # 2. Define the training task
    job = command(
        name=f"lstm-train-{int(time.time())}", # Add a unique name
        code=code_dir, 
        inputs={"hidden_nodes": hidden_nodes},
        command="python train_lstm.py --hidden_nodes ${{inputs.hidden_nodes}}",
        environment="AzureML-sklearn-1.0-ubuntu20.04-py38-cpu@latest",
        compute=compute
    )
    try:
        st.info(f"Submitting job from: {script_folder}")
        returned_job = ml_client.jobs.create_or_update(job)
        st.success(f"Job created! ID: {returned_job.name}")

    except AzureError as e:
        st.error("### Azure Service Error")
        # str(e) is the reliable way to get the message in Python 3.12
        st.code(str(e))
        
        if "Authorization" in str(e) or "403" in str(e):
            st.warning("🔑 **Permission Issue:** Your Web App's Identity likely needs 'Storage Blob Data Contributor' on the workspace storage.")

    except Exception as e:
        st.error(f"### System Error: {type(e).__name__}")
        st.code(str(e))
    """
    try:
        st.info(f"Attempting to submit job with code from: {script_folder}")
        
        # Check if the directory even exists to avoid basic path errors
        if not os.path.exists(code_dir):
            st.error(f"Directory not found: {code_dir}")
        else:
            st.write("Files found:", os.listdir(code_dir))
    
        # 3. Submit the job
        returned_job = ml_client.jobs.create_or_update(job)
        st.info(f"Job started! View here: {returned_job.services['Studio'].endpoint}")

    except AssetException as ae:
        st.error("### Asset Upload Error")
        st.warning("The SDK could not bundle or upload your code folder.")
        st.code(ae.message)
        
        # Check for common Streamlit Cloud/App Service issues
        if "Permission denied" in str(ae):
            st.info("💡 **Tip:** The web app doesn't have write access to its own temp folder. "
                    "Try setting the `code` parameter to a specific folder containing only the script.")

    except MLClientRootException as re:
        st.error("### Azure ML Client Error")
        st.code(re.message)

    except Exception as e:
        st.error(f"### Unexpected Error: {type(e).__name__}")
        st.exception(e) """


