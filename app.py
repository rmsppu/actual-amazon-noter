import os
import subprocess
import tempfile
import uuid
import threading
import time
import sys
import traceback
from flask import Flask, request, render_template, jsonify

# Safe import of kubernetes python client
try:
    from kubernetes import client, config
    HAS_K8S_SDK = True
except ImportError:
    HAS_K8S_SDK = False

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

# Retrieve git commit hash dynamically
commit_hash = None
if os.path.exists("commit_hash.txt"):
    try:
        with open("commit_hash.txt", "r") as f:
            commit_hash = f.read().strip()
    except Exception:
        pass

if not commit_hash:
    try:
        commit_hash = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        commit_hash = "unknown"

@app.route('/')
def index():
    return render_template('index.html', commit_hash=commit_hash)

@app.route('/diagnostics')
def diagnostics():
    import requests
    api_url = os.environ.get('ACTUAL_HTTP_API_URL')
    api_key = os.environ.get('ACTUAL_HTTP_API_KEY')
    sync_id = os.environ.get('ACTUAL_SYNCID')
    
    if not api_url or not api_key or not sync_id:
        return jsonify({
            'status': 'ERROR',
            'error': 'Missing connection environment variables',
            'env_keys_present': {
                'ACTUAL_HTTP_API_URL': bool(api_url),
                'ACTUAL_HTTP_API_KEY': bool(api_key),
                'ACTUAL_SYNCID': bool(sync_id)
            }
        }), 400
        
    try:
        url = api_url.rstrip('/') + f'/v1/budgets/{sync_id}/accounts'
        r = requests.get(url, headers={'x-api-key': api_key}, timeout=5)
        if r.status_code == 200:
            accounts = r.json().get('data', [])
            return jsonify({
                'status': 'OK',
                'api_connection': 'SUCCESS',
                'api_url': api_url,
                'sync_id': sync_id,
                'accounts_count': len(accounts),
                'accounts': [{'id': a.get('id'), 'name': a.get('name'), 'offbudget': a.get('offbudget')} for a in accounts]
            })
        else:
            return jsonify({
                'status': 'ERROR',
                'api_connection': 'FAILED',
                'status_code': r.status_code,
                'response': r.text[:200]
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'ERROR',
            'api_connection': 'EXCEPTION',
            'error': str(e)
        }), 500


@app.route('/process', methods=['POST'])
def process():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    execute = request.form.get('execute') == 'true'
    force = request.form.get('force') == 'true'
    days = request.form.get('days', '')
    amount_tolerance = request.form.get('amount_tolerance', '')
    fmt = request.form.get('format', 'auto')

    # Save to a temporary file, preserving extension for auto-detection
    _, ext = os.path.splitext(file.filename)
    if not ext:
        ext = '.csv'
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f'uploaded_orders{ext}')
    file.save(temp_path)

    try:
        # Prepare subprocess environment, inheriting from current environment
        env = os.environ.copy()
        
        # Build command
        cmd = ['python3', 'actual-ecommerce-noter']
        if execute:
            cmd.append('--execute')
        else:
            cmd.extend(['--dry-run', 'csv'])
            
        if force:
            cmd.append('--force')
            
        if days and days != "Default":
            try:
                days_int = int(days)
                cmd.extend(['--days', str(days_int)])
            except ValueError:
                pass
                
        if amount_tolerance and amount_tolerance != "Default":
            try:
                amt_float = float(amount_tolerance)
                cmd.extend(['--amount-tolerance', f"{amt_float:.2f}"])
            except ValueError:
                pass
        cmd.extend(['--format', fmt])
        cmd.append(temp_path)

        # Run subprocess
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        stdout = result.stdout
        stderr = result.stderr
        success = result.returncode == 0

        # Forward subprocess output to container logs for real-time observability
        if stdout:
            print("--- NOTER STDOUT ---", flush=True)
            print(stdout, flush=True)
        if stderr:
            print("--- NOTER STDERR ---", file=sys.stderr, flush=True)
            print(stderr, file=sys.stderr, flush=True)

        # Clean output a bit (e.g. remove full temporary path references)
        stdout = stdout.replace(temp_path, file.filename)
        stderr = stderr.replace(temp_path, file.filename)

        return jsonify({
            'success': success,
            'stdout': stdout,
            'stderr': stderr,
            'returncode': result.returncode
        })

    except Exception as e:
        print(f"ERROR: Execution failed: {str(e)}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        return jsonify({'error': f'Execution failed: {str(e)}'}), 500
    finally:
        # Ensure temporary file cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

# --- AI Assistant Integration Endpoints ---

active_jobs = {}  # for local mode mock execution

def run_local_mock_job(job_id):
    active_jobs[job_id] = {
        "status": "running",
        "logs": [
            "[Initial Test] local actual-ai-fork mock runner active.",
            f"[Local Adapter] Spawning {job_id}...",
            "[Log Streamer] actual-ai has booted. Fetching live output:",
            "----------------------------------------------------------",
            "Loaded configuration settings...",
            "Connecting to Actual Budget at http://actual-server:5006...",
            "Gemini Model active: gemini-2.5-flash-lite",
            "Scanning transactions..."
        ]
    }
    
    stages = [
        "Matched 8 recurring utility payments...",
        "Matched 5 grocery store annotations...",
        "AI classification score threshold: 0.85",
        "Updating category mappings in Actual server...",
        "Success! Categorized 13 uncategorized transactions.",
        "Job completed successfully."
    ]
    
    for stage in stages:
        time.sleep(1.5)
        active_jobs[job_id]["logs"].append(stage)
        
    active_jobs[job_id]["status"] = "success"

@app.route('/ai/status')
def ai_status():
    namespace = os.environ.get('ACTUAL_AI_NAMESPACE', 'finance')
    cronjob_name = os.environ.get('ACTUAL_AI_CRONJOB_NAME', 'actual-ai')
    
    in_k8s = os.path.exists('/var/run/secrets/kubernetes.io/serviceaccount')
    
    if in_k8s:
        if not HAS_K8S_SDK:
            return jsonify({
                "status": "AI Status: Initial Integration Checked (Kubernetes Mode - Missing SDK)",
                "enabled": False,
                "mode": "Kubernetes",
                "error": "kubernetes python client SDK not installed"
            })
        try:
            config.load_incluster_config()
            batch_v1 = client.BatchV1Api()
            # Read CronJob
            cj = batch_v1.read_namespaced_cron_job(cronjob_name, namespace)
            return jsonify({
                "status": "AI Status: Initial Integration Checked (Kubernetes Mode)",
                "enabled": True,
                "mode": "Kubernetes",
                "cronjob": cronjob_name,
                "namespace": namespace
            })
        except Exception as e:
            return jsonify({
                "status": "AI Status: Initial Integration Missing (Dormant)",
                "enabled": False,
                "mode": "Kubernetes",
                "error": str(e)
            })
    else:
        # Local Mode check
        local_dir_exists = os.path.exists('../actual-ai-fork')
        has_docker = False
        try:
            subprocess.run(['docker', '--version'], capture_output=True, text=True)
            has_docker = True
        except Exception:
            pass
            
        if local_dir_exists or has_docker:
            return jsonify({
                "status": "AI Status: Initial Integration Checked (Local Mode)",
                "enabled": True,
                "mode": "Local",
                "cronjob": cronjob_name,
                "namespace": namespace
            })
        else:
            return jsonify({
                "status": "AI Status: Initial Integration Missing (Dormant)",
                "enabled": False,
                "mode": "Local",
                "error": "No local actual-ai-fork directory or docker command found"
            })

@app.route('/ai/classify', methods=['POST'])
def ai_classify():
    namespace = os.environ.get('ACTUAL_AI_NAMESPACE', 'finance')
    cronjob_name = os.environ.get('ACTUAL_AI_CRONJOB_NAME', 'actual-ai')
    
    in_k8s = os.path.exists('/var/run/secrets/kubernetes.io/serviceaccount')
    
    if in_k8s:
        if not HAS_K8S_SDK:
            return jsonify({"error": "kubernetes library not available"}), 500
        try:
            config.load_incluster_config()
            batch_v1 = client.BatchV1Api()
            
            # Fetch existing CronJob
            cj = batch_v1.read_namespaced_cron_job(cronjob_name, namespace)
            
            # Extract pod spec template from CronJob
            pod_template = cj.spec.job_template.spec.template
            
            # Generate unique job name
            unique_suffix = uuid.uuid4().hex[:6]
            job_name = f"{cronjob_name}-manual-{unique_suffix}"
            
            # Construct ownerReference linking Job back to parent CronJob
            owner_reference = client.V1OwnerReference(
                api_version=cj.api_version or "batch/v1",
                block_owner_deletion=True,
                controller=True,
                kind=cj.kind or "CronJob",
                name=cj.metadata.name,
                uid=cj.metadata.uid
            )
            
            # Create Job resource manifest
            job_manifest = client.V1Job(
                api_version="batch/v1",
                kind="Job",
                metadata=client.V1ObjectMeta(
                    name=job_name,
                    namespace=namespace,
                    owner_references=[owner_reference],
                    labels={
                        "app.kubernetes.io/managed-by": "actual-ecommerce-noter",
                        "cronjob-name": cronjob_name
                    }
                ),
                spec=client.V1JobSpec(
                    template=pod_template,
                    backoff_limit=0
                )
            )
            
            # Submit to K8s
            batch_v1.create_namespaced_job(namespace, job_manifest)
            
            return jsonify({
                "success": True,
                "job_id": job_name,
                "mode": "Kubernetes"
            })
            
        except Exception as e:
            return jsonify({"error": f"Failed to spawn K8s job: {str(e)}"}), 500
    else:
        # Spawn mock local job
        job_id = f"{cronjob_name}-manual-{uuid.uuid4().hex[:6]}"
        thread = threading.Thread(target=run_local_mock_job, args=(job_id,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True,
            "job_id": job_id,
            "mode": "Local"
        })

# In-memory cache for K8s logs to prevent losing them when the pod is deleted
k8s_job_logs_cache = {}

@app.route('/ai/logs/<job_id>')
def ai_logs(job_id):
    namespace = os.environ.get('ACTUAL_AI_NAMESPACE', 'finance')
    in_k8s = os.path.exists('/var/run/secrets/kubernetes.io/serviceaccount')
    
    if in_k8s:
        if not HAS_K8S_SDK:
            return jsonify({"error": "kubernetes library not available"}), 500
        try:
            config.load_incluster_config()
            core_v1 = client.CoreV1Api()
            batch_v1 = client.BatchV1Api()
            
            # 1. Check if we already have a cached completed/failed state for this job
            if job_id in k8s_job_logs_cache:
                cached = k8s_job_logs_cache[job_id]
                if cached["status"] in ["success", "failed"]:
                    return jsonify(cached)

            # 2. Query K8s for the Job status first to see if it failed/completed
            job_failed = False
            job_success = False
            try:
                job = batch_v1.read_namespaced_job(job_id, namespace)
                if job.status.failed and job.status.failed > 0:
                    job_failed = True
                elif job.status.succeeded and job.status.succeeded > 0:
                    job_success = True
            except Exception as e:
                # If Job resource is completely gone, fallback to cache or report failed
                if job_id in k8s_job_logs_cache:
                    return jsonify(k8s_job_logs_cache[job_id])
                return jsonify({"error": f"Job not found: {str(e)}"}), 404

            # 3. Find the pod associated with this job
            pods = core_v1.list_namespaced_pod(
                namespace,
                label_selector=f"job-name={job_id}"
            )
            
            if not pods.items:
                # If no pods are found, but the Job was marked as failed or success,
                # we return the cached log (or a failed message if no logs were cached)
                if job_failed:
                    logs_msg = k8s_job_logs_cache.get(job_id, {}).get("logs", "Job failed and its pod was deleted before logs could be fully read.")
                    res = {"status": "failed", "logs": logs_msg}
                    k8s_job_logs_cache[job_id] = res
                    return jsonify(res)
                elif job_success:
                    logs_msg = k8s_job_logs_cache.get(job_id, {}).get("logs", "Job completed successfully.")
                    res = {"status": "success", "logs": logs_msg}
                    k8s_job_logs_cache[job_id] = res
                    return jsonify(res)
                
                # Otherwise, it might be still waiting to create the pod
                return jsonify({
                    "status": "pending",
                    "logs": f"Job {job_id} has been queued. Waiting for Pod creation..."
                })
                
            pod = pods.items[0]
            pod_name = pod.metadata.name
            phase = pod.status.phase
            
            if phase == "Pending":
                return jsonify({
                    "status": "pending",
                    "logs": f"Pod {pod_name} is starting up (Phase: Pending)..."
                })
            
            # Fetch logs
            try:
                logs_text = core_v1.read_namespaced_pod_log(pod_name, namespace)
            except Exception as e:
                logs_text = f"Could not retrieve pod logs: {str(e)}"
                
            status_map = {
                "Running": "running",
                "Succeeded": "success",
                "Failed": "failed"
            }
            status = status_map.get(phase, "running")
            
            # If the job status was checked as failed/success, override phase
            if job_failed:
                status = "failed"
            elif job_success:
                status = "success"

            # Cache the logs
            res = {
                "status": status,
                "logs": logs_text
            }
            k8s_job_logs_cache[job_id] = res
            
            return jsonify(res)
            
        except Exception as e:
            return jsonify({"error": f"Failed to retrieve K8s logs: {str(e)}"}), 500
    else:
        # Local mock retrieval
        if job_id in active_jobs:
            job_info = active_jobs[job_id]
            return jsonify({
                "status": job_info["status"],
                "logs": "\n".join(job_info["logs"])
            })
        else:
            return jsonify({"error": "Job ID not found"}), 404

@app.errorhandler(Exception)
def handle_exception(e):
    # Print unhandled exceptions to container logs for real-time observability
    print("--- UNHANDLED EXCEPTION ---", file=sys.stderr, flush=True)
    traceback.print_exc(file=sys.stderr)
    sys.stderr.flush()
    
    # Return JSON to prevent HTML error pages breaking JSON.parse on the frontend
    response = jsonify({
        "success": False,
        "error": str(e),
        "traceback": traceback.format_exc()
    })
    return response, 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
