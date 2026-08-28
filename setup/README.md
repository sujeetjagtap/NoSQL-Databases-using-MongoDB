# Environment Setup Guide

This directory is your starting point before Chapter 1. It covers two things:

1. **Installing MongoDB itself**, natively, on every major platform (Linux distributions, Windows, macOS) plus an honest look at BSD and Redox OS, where "native install" isn't really the right answer.
2. **Every additional tool** used somewhere across the 18 chapters and the appendix (Docker, Terraform, `mongosh`, the MongoDB Database Tools, OpenSSL, Neo4j, Ollama, and so on), with a chapter-by-chapter map so you only install what you actually need, when you need it.

If you'd rather skip all of this and get a working MongoDB in under a minute, jump to [The Fast Path: Docker](#the-fast-path-docker) below -- it works identically regardless of your OS and is what the repo's own Quick Start recommends.

Once you've installed something, **verify it** with `python chapter-02/lab_01_setup_environment.py` -- it's an automated checklist (Python version, PyMongo, local MongoDB, Atlas, Docker, optional packages) built for exactly this purpose. Don't guess whether a manual install worked; run the checker.

---

## The Fast Path: Docker

Regardless of which OS you're on, this gets you a running MongoDB 7 in one command, with nothing to configure:

```bash
docker run -d -p 27017:27017 --name mongo mongo:7
```

This is the recommended path for Chapters 1-7 and any chapter where you just need "a MongoDB to connect to." Chapters 8, 9, 12, and 13 have their own `docker-compose` files for multi-container setups (replica sets, production-shaped deployments) -- you don't need to set those up in advance, each chapter's README walks you through it when you get there.

If you don't have Docker yet, see [Docker / Docker Compose](#docker--docker-compose) under Additional Requirements below.

---

## Installing MongoDB Natively

Native installs are worth doing if you want MongoDB running as a persistent background service without Docker, or if you're on a platform where Docker itself is awkward. The commands below reflect the current standard installation method for each platform as of this writing -- MongoDB's official package repository URLs are versioned by both MongoDB release and OS codename, so if a command below fails, check [MongoDB's official install docs](https://www.mongodb.com/docs/manual/administration/install-community/) for your exact OS version before assuming something else is wrong.

### Debian / Ubuntu (APT)

```bash
# 1. Import MongoDB's public GPG key
curl -fsSL https://pgp.mongodb.com/server-7.0.asc | \
  sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor

# 2. Add the MongoDB repository (replace 'jammy' with your Ubuntu/Debian codename)
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] \
  https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
  sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# 3. Install and start
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl enable --now mongod
```

Find your codename with `lsb_release -cs` (Ubuntu) or `cat /etc/os-release` (Debian). For Debian, the repo path is `https://repo.mongodb.org/apt/debian` instead of `.../ubuntu`.

### RedHat / CentOS / Fedora / RHEL (YUM/DNF)

```bash
# 1. Add the MongoDB repo file
sudo tee /etc/yum.repos.d/mongodb-org-7.0.repo <<'EOF'
[mongodb-org-7.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/7.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://pgp.mongodb.com/server-7.0.asc
EOF

# 2. Install and start
sudo dnf install -y mongodb-org   # or: sudo yum install -y mongodb-org
sudo systemctl enable --now mongod
```

### BSD (FreeBSD, OpenBSD, NetBSD)

**Be aware before you start:** MongoDB Inc. does not build or officially support MongoDB on any BSD. FreeBSD's own package repository (`pkg install mongodbXX`) still has entries, but the `databases/mongodb` port has been deprecated/expired upstream, and the newest package version generally available is from the 5.0.x line -- multiple major versions behind current MongoDB (8.x). If you need current features (recent aggregation operators, current vector search support, etc.), a BSD-native install will not get you there.

If you still want a native FreeBSD install for the earlier chapters (which don't depend on newer features):

```sh
su -
pkg update
pkg install mongodb50   # or check `pkg search mongodb` for the newest available version
sysrc mongod_enable="YES"
service mongod start
```

OpenBSD and NetBSD have no actively maintained MongoDB package at all. For any BSD, the more reliable path -- and the one we'd actually recommend -- is:
- **Run MongoDB in a Linux VM or jail** (`bhyve`, `VirtualBox`, or a FreeBSD jail running a Linux-compatible layer) and install it there using the Debian/RedHat instructions above, or
- **Skip local MongoDB entirely and use Atlas** (see below) -- your BSD machine only needs Python and network access, not a locally running `mongod`.

### Windows

**Option A -- MSI installer (native Windows service):**
Download the installer from [mongodb.com/try/download/community](https://www.mongodb.com/try/download/community), run it, and choose "Install MongoDB as a Service" during setup -- this handles the Windows Service registration and startup automatically, and installs MongoDB Compass alongside it if you leave that box checked.

**Option B -- winget:**
```powershell
winget install MongoDB.Server
```

**Option C (recommended for this book specifically) -- WSL2:**
Every shell script in this repo (Chapters 8, 9, 12, 13) is written for a POSIX shell. If you're on Windows, installing MongoDB inside WSL2 (Windows Subsystem for Linux) and following the Debian/Ubuntu instructions above -- rather than installing MongoDB natively on Windows -- means every lab in this repo, including the `.sh` scripts, works without translation. Install WSL2 with `wsl --install` from an elevated PowerShell prompt, then follow the Ubuntu instructions above inside it.

### macOS (Homebrew)

```bash
brew tap mongodb/brew
brew install mongodb-community@7.0
brew services start mongodb-community@7.0
```

Apple Silicon (M1/M2/M3/M4) and Intel Macs are both supported by the same Homebrew formula.

### Redox OS

**Short answer: don't try to run MongoDB natively on Redox for these labs.** Here's why, and what to do instead.

Redox OS is an experimental, hobbyist microkernel operating system written in Rust. It has its own C standard library (`relibc`, not glibc), its own package manager (`pkgutils`/Cookbook), and while it does have a growing set of ported packages -- including CPython, via a `python` recipe template in Cookbook -- there is no MongoDB package, and no evidence of anyone having ported MongoDB's C++ codebase (and its WiredTiger storage engine, which assumes a fairly complete POSIX threading and filesystem implementation) to Redox. As one prominent OS researcher put it in 2025, Redox "has real potential, but it is not there yet." Compiling MongoDB's full C++ toolchain from source against `relibc` is not a realistic weekend project, and isn't something this repo's labs assume you'll do.

Redox also doesn't run Linux containers natively (it's not Linux-kernel-compatible), so `docker run mongo:7` isn't an option on Redox itself either.

**What actually works if you want to use Redox:**
1. **Run Redox as a guest VM** (its own documentation's standard workflow uses QEMU) alongside a second VM or your host machine running a supported OS with MongoDB installed, and connect to that MongoDB over the network from Redox.
2. **Use MongoDB Atlas** (see below) and connect from Redox's Python port. This is genuinely worth trying if you want to explore Redox specifically -- Redox's CPython recipe plus `pip install pymongo` may well work for pure network I/O, since PyMongo degrades gracefully to a pure-Python BSON implementation when its optional C extensions aren't available. We haven't verified this combination ourselves, so treat it as an experiment, not a guaranteed path -- if you try it, we'd genuinely like to hear how it goes.
3. **Simplest of all: don't run the labs from Redox.** Use a supported OS for the labs, and treat Redox as a separate, independent exploration.

---

## MongoDB Atlas (Cloud) -- The Platform-Independent Alternative

Every platform above can skip a native or Docker install entirely and instead use a free-tier MongoDB Atlas cluster:

1. Create a free account at [mongodb.com/cloud/atlas/register](https://www.mongodb.com/cloud/atlas/register)
2. Create a free M0 cluster (this is exactly what Chapter 13's Terraform lab automates)
3. Add your current IP to the cluster's Network Access list (or `0.0.0.0/0` for lab purposes only -- never for a real deployment)
4. Create a database user and copy the connection string into `MONGO_URI` in your `.env` file

Atlas is the only realistic path for BSD and Redox OS, and it's what Chapters 2 and 13 use to introduce cloud-hosted, managed databases regardless of which OS you're following along on.

---

## Additional Requirements

Beyond MongoDB itself, different chapters need different additional tools. Install these as you reach the chapter that needs them -- nothing here is needed before Chapter 1.

| Tool | Needed for | Linux | macOS | Windows |
|---|---|---|---|---|
| **Python 3.10+** | Every chapter | `sudo apt install python3 python3-pip` (Debian/Ubuntu) or `sudo dnf install python3` (RHEL/Fedora) | `brew install python@3.12` | [python.org/downloads](https://www.python.org/downloads/) or `winget install Python.Python.3.12` |
| **pip packages** | Every chapter | `pip install -r requirements.txt --break-system-packages` (or use a venv) | same | same |
| **Docker + Docker Compose** | Ch 8, 13, Appendix A (and the fast path above) | [docs.docker.com/engine/install](https://docs.docker.com/engine/install/) (per-distro instructions) | Docker Desktop, or `brew install --cask docker` | Docker Desktop (`winget install Docker.DockerDesktop`), requires WSL2 backend |
| **mongosh** | Ch 8, 9, 12, 13 | Installed automatically with `mongodb-org` above, or `sudo apt install mongodb-mongosh` | `brew install mongosh` | Bundled with the MSI installer, or `winget install MongoDB.Shell` |
| **MongoDB Database Tools** (`mongodump`/`mongorestore`) | Ch 14 | `sudo apt install mongodb-database-tools` (or per RedHat repo above) | `brew install mongodb-database-tools` | [mongodb.com/try/download/database-tools](https://www.mongodb.com/try/download/database-tools) |
| **OpenSSL** | Ch 12 | Usually preinstalled; `sudo apt install openssl` if not | Usually preinstalled; `brew install openssl` if not | `winget install ShiningLight.OpenSSL` or use WSL2 |
| **Terraform** | Ch 13 | `sudo apt install terraform` (after adding HashiCorp's apt repo -- see [developer.hashicorp.com/terraform/install](https://developer.hashicorp.com/terraform/install)) | `brew install terraform` | `winget install HashiCorp.Terraform` |
| **kubectl + a cluster** | Ch 13 (optional -- the lab generates manifests either way) | `sudo apt install kubectl`, plus [minikube](https://minikube.sigs.k8s.io/) or [kind](https://kind.sigs.k8s.io/) for a local cluster | `brew install kubectl minikube` | `winget install Kubernetes.kubectl` |
| **Neo4j** | Ch 16, 18 (optional -- labs fall back to estimates/in-memory graph without it) | [Neo4j Desktop](https://neo4j.com/download/) or `docker run neo4j:5` | same | same |
| **Cassandra** | Ch 16, 18 (referenced architecturally; not required to run any lab) | [cassandra.apache.org/download](https://cassandra.apache.org/_/download.html) or `docker run cassandra:5` | same | same |
| **Ollama** (local LLM) | Ch 17, Appendix A (optional -- OpenAI API key is the alternative) | [ollama.com/download](https://ollama.com/download/linux) | `brew install ollama` | [ollama.com/download](https://ollama.com/download/windows) |

For any tool above, `docker run <image>` is usually the fastest way to get it running for lab purposes without a native install -- this repo's own labs are written to work against either.

---

## Verifying Everything

Once MongoDB is running (natively, via Docker, or via Atlas) and you've installed whatever Chapter 2 onward needs:

```bash
pip install -r requirements.txt --break-system-packages
python chapter-02/lab_01_setup_environment.py
```

This is the same automated checklist referenced in Chapter 2's own README -- it checks your Python version, PyMongo, local MongoDB reachability, Atlas reachability (if `MONGO_URI_ATLAS` is set), Docker availability, and which of the optional packages (FastAPI, Streamlit, Neo4j driver, etc.) are already installed. Fix whatever it flags before moving on to Chapter 1's labs.

---

## Platform Support Summary

| Platform | MongoDB Support | Recommended Path |
|---|---|---|
| Debian / Ubuntu | Official, current | Native install (APT) or Docker |
| RHEL / CentOS / Fedora | Official, current | Native install (YUM/DNF) or Docker |
| FreeBSD | Community package, several major versions behind | Docker via a Linux VM/jail, or Atlas |
| OpenBSD / NetBSD | None | Atlas, or a Linux VM |
| Windows | Official, current | WSL2 + native Linux install (best lab compatibility), Docker Desktop, or the native MSI |
| macOS (Intel & Apple Silicon) | Official, current | Native install (Homebrew) or Docker Desktop |
| Redox OS | None -- experimental OS, no known port | Atlas from Redox's Python port (experimental), or run the labs from a different OS entirely |
