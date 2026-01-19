# DropDeep — Full Project Context for AI, Documentation & Backup

## What Is DropDeep?

**DropDeep** is a desktop tool that scans any project folder and exports its **full structure + code** in a clean, readable format.

It is built to solve one core problem:

> **AI and humans fail to understand projects when context is incomplete or unstructured.**

DropDeep prepares **complete, controlled, AI-ready project context** — without zipping folders or uploading files one by one.

Everything runs **locally**.

---

## ⭐ Top 3 Core Features (Why People Use DropDeep)

### 🥇 1. AI-Ready Full Project Context (No Confusion)

DropDeep exports:

* full folder tree
* exact file paths & names
* readable code content (safe & ordered)

**Why it matters:**
AI understands the *whole project*, not random snippets.

---

### 🥈 2. Token Estimation Before Export (AI-Safe)

DropDeep estimates how many **AI tokens** your export will use **before you export**.

**Why it matters:**
You avoid AI errors like *"input too long"* or silent truncation.

---

### 🥉 3. Ignore Files & Folders (Full Control)

You decide **what is included and excluded**:

* folders (`node_modules`, `dist`)
* file types (`*.png`, `*.log`)
* generated or noisy files

**Why it matters:**
Cleaner exports, fewer tokens, better AI results.

---

## What Problems Does DropDeep Solve?

| Problem                    | How DropDeep Fixes It          |
| -------------------------- | ------------------------------ |
| AI gets confused           | Full structure + code in order |
| Zips are useless for AI    | AI-ready text output           |
| Files missed accidentally  | Controlled scanning            |
| Token limits hit           | Token estimation before export |
| Large projects crash tools | Safe scanning with limits      |

---

## Key Features (Explained Simply)

### 📁 Project Scanning

* Scans folders safely
* Handles large projects
* Pause / resume / stop anytime

**Useful for:** big repos, legacy code, monorepos

---

### 🌲 Accurate Folder Tree

* Preserves exact hierarchy
* Keeps file relationships clear

**Useful for:** AI understanding architecture, human clarity

---

### 📄 Code Preview (VS Code-Like)

* Click a file → preview instantly
* Syntax-highlighted code
* Image preview for assets

**Useful for:** quick inspection without opening IDE

---

### 🚫 Ignore Files & Folders

* Advanced ignore patterns
* Supports glob rules (`*.png`, `dist/`)
* Persistent across sessions

**Useful for:** removing noise, saving tokens

---

### 🧠 AI-Ready Export System

Export formats:

* **Full Structure + Code**
* **Tree Only**
* **JSON**
* **PDF (with TOC & bookmarks)**

**Useful for:** AI prompts, documentation, audits

---

### 🔢 Token Estimation (Short & Clear)

**What are tokens?**
AI reads text in *tokens* (not pages or files). Large text = more tokens.

**Example (Gemini):**

* Too many tokens → AI rejects or cuts input
* Cut input → wrong answers

**What DropDeep does:**

* estimates tokens before export
* helps you choose safer formats (tree vs full)
* prevents failed AI prompts

**Result:**
You export only what AI can safely understand.

---

### 🔍 Search & Filter

* Search files instantly
* Filter large trees in real time

---

### 📦 One-File Backup

* Export entire project into one readable file
* Archive code outside Git

**Useful for:** long-term backup, sharing, documentation

---

## Common Use Cases

| Use Case               | How DropDeep Helps         |
| ---------------------- | -------------------------- |
| AI project explanation | Full context in one export |
| Refactoring with AI    | No missing files           |
| Documentation          | Clean, structured output   |
| Onboarding             | Easy project understanding |
| Backup                 | One readable snapshot      |

---

## What DropDeep Is NOT

* ❌ Not an IDE
* ❌ Not a code editor
* ❌ Not an AI model
* ❌ Not a cloud service

It does **one job**:
**prepare perfect project context**.

---

## Why DropDeep Instead of Zipping?

| Zip File           | DropDeep            |
| ------------------ | ------------------- |
| AI can't read      | AI-ready text       |
| Structure hidden   | Structure preserved |
| Manual cleanup     | Automatic           |
| No token awareness | Token estimate      |

---

## Installation

### Prerequisites
- Python 3.8+
- Windows / macOS / Linux

### Setup

```bash
git clone https://github.com/abdulkarim20-ui/dropdeep.git
cd dropdeep
pip install -r requirements.txt
python main.py
```

---

## Usage

1. Launch DropDeep
2. Drag & drop a project folder (or browse)
3. Review structure and preview files
4. Select export formats
5. Export safely with size warnings and token estimates

---

## Project Structure

```
DropDeep/
├── assets/
├── src/
│   ├── backend/
│   │   ├── analyzers/
│   │   └── managers/
│   ├── frontend/
│   │   ├── components/
│   │   └── styles/
│   └── config.py
├── ignore_patterns.json
├── main.py
└── requirements.txt
```

---

## Tech Stack

* Python
* PyQt5 (Desktop UI)
* QScintilla (Code preview)
* ReportLab (PDF export)

Runs **fully offline**.

---

## Philosophy

> **AI is only as good as the context you give it.**
> DropDeep exists to give *clean, complete, controlled context*.

---

## Who Should Use DropDeep?

* Developers using AI seriously
* Teams documenting real projects
* Engineers exploring unfamiliar code
* Anyone tired of broken AI context

---

## License

MIT License — free for personal and commercial use.

---

## Author

Created and maintained by **Abdulkarim Shaikh**

- GitHub: [https://github.com/abdulkarim20-ui](https://github.com/abdulkarim20-ui)
