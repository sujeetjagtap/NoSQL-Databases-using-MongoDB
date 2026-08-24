"""Lab 13.2 - Kubernetes StatefulSet for MongoDB

Deploys a 3-member MongoDB replica set on Kubernetes as a StatefulSet.
Unlike Docker Compose (Lab 13.1), Kubernetes gives each pod a stable
network identity (mongo-0, mongo-1, mongo-2), a headless Service for
peer discovery, and per-pod persistent storage via volumeClaimTemplates
that survives pod restarts and rescheduling.

This script GENERATES the manifests (so they can be reviewed, version
controlled, and diffed like any other infrastructure change) and then,
if `kubectl` is available and configured against a cluster, applies them
and waits for the StatefulSet to become ready. If no cluster is available
it stops after generating the manifests and prints the commands to run
by hand -- the lab is still useful for reading the manifests even without
a live cluster.
"""

import sys, os, subprocess, shutil, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection import banner

NAMESPACE = "nosql-labs"
STATEFULSET_NAME = "mongo"
REPLICAS = 3
MANIFEST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "k8s")

HEADLESS_SERVICE_YAML = f"""\
apiVersion: v1
kind: Service
metadata:
  name: {STATEFULSET_NAME}
  namespace: {NAMESPACE}
  labels:
    app: {STATEFULSET_NAME}
spec:
  clusterIP: None          # Headless: gives each pod its own stable DNS name
  ports:
    - port: 27017
      name: mongod
  selector:
    app: {STATEFULSET_NAME}
"""

STATEFULSET_YAML = f"""\
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: {STATEFULSET_NAME}
  namespace: {NAMESPACE}
spec:
  serviceName: {STATEFULSET_NAME}
  replicas: {REPLICAS}
  selector:
    matchLabels:
      app: {STATEFULSET_NAME}
  template:
    metadata:
      labels:
        app: {STATEFULSET_NAME}
    spec:
      terminationGracePeriodSeconds: 30
      containers:
        - name: mongod
          image: mongo:7.0
          command:
            - mongod
            - "--replSet=rs0"
            - "--bind_ip_all"
          ports:
            - containerPort: 27017
              name: mongod
          volumeMounts:
            - name: mongo-data
              mountPath: /data/db
          resources:
            requests:
              cpu: "250m"
              memory: "512Mi"
            limits:
              cpu: "1"
              memory: "1Gi"
          readinessProbe:
            exec:
              command: ["mongosh", "--quiet", "--eval", "db.runCommand({{ping:1}})"]
            initialDelaySeconds: 10
            periodSeconds: 10
          livenessProbe:
            exec:
              command: ["mongosh", "--quiet", "--eval", "db.runCommand({{ping:1}})"]
            initialDelaySeconds: 30
            periodSeconds: 20
  volumeClaimTemplates:
    - metadata:
        name: mongo-data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 5Gi
"""

INIT_JOB_YAML = f"""\
apiVersion: batch/v1
kind: Job
metadata:
  name: {STATEFULSET_NAME}-rs-init
  namespace: {NAMESPACE}
spec:
  backoffLimit: 3
  template:
    spec:
      restartPolicy: OnFailure
      containers:
        - name: rs-init
          image: mongo:7.0
          command:
            - mongosh
            - "--host={STATEFULSET_NAME}-0.{STATEFULSET_NAME}.{NAMESPACE}.svc.cluster.local"
            - "--eval"
            - >
              rs.initiate({{
                _id: "rs0",
                members: [
                  {{_id: 0, host: "{STATEFULSET_NAME}-0.{STATEFULSET_NAME}.{NAMESPACE}.svc.cluster.local:27017"}},
                  {{_id: 1, host: "{STATEFULSET_NAME}-1.{STATEFULSET_NAME}.{NAMESPACE}.svc.cluster.local:27017"}},
                  {{_id: 2, host: "{STATEFULSET_NAME}-2.{STATEFULSET_NAME}.{NAMESPACE}.svc.cluster.local:27017"}}
                ]
              }})
"""

NAMESPACE_YAML = f"""\
apiVersion: v1
kind: Namespace
metadata:
  name: {NAMESPACE}
"""

MANIFESTS = {
    "00-namespace.yaml": NAMESPACE_YAML,
    "01-headless-service.yaml": HEADLESS_SERVICE_YAML,
    "02-statefulset.yaml": STATEFULSET_YAML,
    "03-replicaset-init-job.yaml": INIT_JOB_YAML,
}


def write_manifests():
    """Write all manifest files to chapter-13/k8s/ for review and version control."""
    os.makedirs(MANIFEST_DIR, exist_ok=True)
    paths = []
    for filename, content in MANIFESTS.items():
        path = os.path.join(MANIFEST_DIR, filename)
        with open(path, "w") as f:
            f.write(content)
        paths.append(path)
        print(f"  [OK] Wrote {path}")
    return paths


def kubectl_available() -> bool:
    """Check whether kubectl is installed and can reach a cluster."""
    if shutil.which("kubectl") is None:
        return False
    result = subprocess.run(
        ["kubectl", "cluster-info"], capture_output=True, text=True, timeout=10
    )
    return result.returncode == 0


def apply_manifests():
    """Apply manifests in order and wait for the StatefulSet to be ready."""
    for filename in MANIFESTS:
        path = os.path.join(MANIFEST_DIR, filename)
        print(f"\n  Applying {filename} ...")
        result = subprocess.run(
            ["kubectl", "apply", "-f", path], capture_output=True, text=True
        )
        print(f"  {result.stdout.strip() or result.stderr.strip()}")
        if result.returncode != 0:
            print(f"  [ERROR] kubectl apply failed for {filename}")
            return False
        # The init Job must wait for pods to exist and be ready first.
        if filename == "02-statefulset.yaml":
            print(f"\n  Waiting for StatefulSet/{STATEFULSET_NAME} pods to become ready "
                  f"(up to 180s)...")
            wait = subprocess.run(
                [
                    "kubectl", "rollout", "status",
                    f"statefulset/{STATEFULSET_NAME}",
                    "-n", NAMESPACE, "--timeout=180s",
                ],
                capture_output=True, text=True,
            )
            print(f"  {wait.stdout.strip() or wait.stderr.strip()}")
            if wait.returncode != 0:
                print("  [ERROR] StatefulSet did not become ready in time.")
                return False
    return True


def verify_cluster():
    """Confirm the replica set formed correctly by checking rs.status() inside pod 0."""
    print("\n  Verifying replica set status from mongo-0 ...")
    result = subprocess.run(
        [
            "kubectl", "exec", "-n", NAMESPACE, f"{STATEFULSET_NAME}-0", "--",
            "mongosh", "--quiet", "--eval",
            "rs.status().members.forEach(m => print(m.name, m.stateStr))",
        ],
        capture_output=True, text=True,
    )
    print(result.stdout or result.stderr)


def print_manual_instructions():
    print("\n  No live Kubernetes cluster detected (kubectl not installed or not")
    print("  configured). The manifests have still been generated under:")
    print(f"    {MANIFEST_DIR}/")
    print("\n  To try this against a real cluster (e.g. minikube, kind, or a")
    print("  managed cluster on AWS/GCP/Azure), run:")
    print(f"    kubectl apply -f {MANIFEST_DIR}/00-namespace.yaml")
    print(f"    kubectl apply -f {MANIFEST_DIR}/01-headless-service.yaml")
    print(f"    kubectl apply -f {MANIFEST_DIR}/02-statefulset.yaml")
    print(f"    kubectl rollout status statefulset/{STATEFULSET_NAME} -n {NAMESPACE}")
    print(f"    kubectl apply -f {MANIFEST_DIR}/03-replicaset-init-job.yaml")
    print(f"    kubectl exec -n {NAMESPACE} -it {STATEFULSET_NAME}-0 -- "
          f"mongosh --eval 'rs.status()'")


def main():
    banner("Lab 13.2: Kubernetes StatefulSet for MongoDB")

    print("=== Step 1: Generate Kubernetes manifests ===")
    write_manifests()

    print("\n=== Step 2: Check for a reachable Kubernetes cluster ===")
    if kubectl_available():
        print("  [OK] kubectl is installed and a cluster is reachable.")
        print("\n=== Step 3: Apply manifests and wait for rollout ===")
        if apply_manifests():
            verify_cluster()
        else:
            print("\n  [ERROR] Deployment failed -- inspect the errors above and re-run.")
    else:
        print_manual_instructions()

    print("\n  Key difference from Lab 13.1 (Docker Compose):")
    print("  - Docker Compose containers get random restart IPs; StatefulSet pods")
    print("    keep stable DNS names (mongo-0, mongo-1, mongo-2) across restarts,")
    print("    which is what makes a replica set config survive a pod reschedule.")
    print("  - volumeClaimTemplates give each pod its OWN PersistentVolumeClaim,")
    print("    so data isn't lost or shared incorrectly when a pod is recreated.")

    banner("Lab 13.2 Complete")


if __name__ == "__main__":
    main()
