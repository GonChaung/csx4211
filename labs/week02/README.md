# Lab 2 (Week 2): Follow your check-in through the data engineering lifecycle

**Saturday 21 November 2026 ·  Run the lab in codespace and joins AWS Academy with au.edu account.**

On 7 November you checked in to class with your phone. Those check-ins are real data, and a small pipeline turned them into the attendance list. In this lab you run that pipeline yourself, find two problems that really happened on that day, and fix them. At the end you join AWS Academy, the free AWS environment for our cloud labs later in the semester.

By the end of this lab you can:

1. name the lifecycle stage of each step of a real pipeline,
2. find data quality problems with SQL and fix them by re-running the pipeline,
3. explain how a student who never checked in still gets an A (absent), and
4. start your own AWS sandbox (AWS Academy Learner Lab, AWS Data Engineering) and end it safely.

> **Real data:** these are the real check-ins of 7 November, so your own check-in is in them. Look for your student ID. Names are not included. Because the data is real, it is not on GitHub: you download it from MS Teams in Part A. Use it only for this course and do not share it.

Submit the **CSX4211/ITX4211 Lab 2 check** in MS Teams (Assignments) by **Monday 23 November at 23:59**. It is one quiz: you answer 11 questions (questions 7–11 are the lifecycle table from Part C) and upload **4 screenshots** that you take during the lab (marked **Screenshot 1** to **Screenshot 4** below). Several answers come from running the code, so do the steps instead of guessing. You can submit only once, so have all 4 screenshots ready first.

**How to take the screenshots:** first make the terminal bigger with the **^** button at the top right of the terminal panel, so that everything fits. Windows: **Win + PrtScn** saves the whole screen in Pictures → Screenshots. Mac: **Cmd + Shift + 3** saves it on the Desktop. Does it still not fit on one screen? You can upload 2 images for that screenshot.

---

## Part A: Get this week's lab and data (about 10 minutes)

1. Go to https://github.com/codespaces and reopen **the same codespace** as last week, the one you created in Lab 1. Do not create a new one. No codespace yet because you missed Lab 1? Do Part A of `labs/week01/README.md` first.
2. In the terminal, download the new lab code:

```bash
git pull
ls labs/week02
```

You should see `README.md`, `checkin_pipeline.py`, `query.py` and a `data` folder.

3. Get the data. It is real class data, so it is not on GitHub, where anyone can read it. It is in MS Teams:
   - Open your class team → **Files** → **Class Materials** and download **`lab2_data.zip`**.
   - In the codespace **Explorer** (left), open `labs/week02/data` and drag `lab2_data.zip` onto the folder **`export`**.
   - Unzip it and check:

```bash
python -m zipfile -e labs/week02/data/export/lab2_data.zip labs/week02/data/export
ls labs/week02/data/export
```

You should see `checkins_2026-11-07.csv`, `roster_v1.csv`, `roster_v2.csv` and `sessions.csv`. Did your laptop unzip the file by itself? Then drag the four CSV files onto `export` instead.

---

## Part B: Meet the raw data (about 10 minutes)

The check-in form saved one row each time someone pressed **Submit**. The instructor exported those rows to the CSV files you unzipped in Part A:

```bash
ls labs/week02/data/export
head -5 labs/week02/data/export/checkins_2026-11-07.csv
wc -l labs/week02/data/export/checkins_2026-11-07.csv
```

| File | What is inside |
|---|---|
| `checkins_2026-11-07.csv` | every form response on 7 Nov: time, e-mail, section, the ID you typed, the code |
| `roster_v1.csv` | the class lists printed on 6 Nov (CSX4211 only) |
| `roster_v2.csv` | the class lists after 7 Nov (CSX4211 + ITX4211) |
| `sessions.csv` | when the form opened and closed for each section, and the code |

With your partner, answer:

- **Generation:** which system created these rows, and who were the "users" who generated them?
- Each row has the student ID **twice**: once in `Email Address`, once in `Student ID`. Why could they differ?
- `sessions.csv` has a row from 6 Nov marked `test`. Should it count as a class?

---

## Part C: Run the pipeline (about 15 minutes)

```bash
python labs/week02/checkin_pipeline.py
```

You see five kinds of log lines: `[extract]`, `[load]`, `[transform]`, `[check]` and `[serve]`, then a small summary table with the present, absent and percent present for each section. Note the two **WARNING** lines; you investigate them in Part D. The three `[serve]` lines say who gets the result; you use them in Part E, step 5.

> **Screenshot 1 for the lab check:** the end of this first run, with the two WARNING lines, the summary table and the line `Pipeline finished: run by @<your GitHub name> ...`.

Open `labs/week02/checkin_pipeline.py` and read it from the top. With your partner, copy this table into your notes and fill it in. The lab check asks for the **Where** column (questions 7–11: which function does each stage?):

| Lifecycle stage | Where does it happen? (function or line) | What could go wrong here in a real company? |
|---|---|---|
| Generation | | |
| Ingestion | | |
| Storage | | |
| Transformation | | |
| Serving | | |

Look closely at step 5 in `transform()`. Absent students have **no row at all** in the check-in data. Which join makes them appear in the `attendance` table anyway?

Now find yourself. Replace `YOUR_ID` with your 7-digit student ID:

```bash
python labs/week02/query.py "SELECT * FROM checkins WHERE email_id = 'YOUR_ID'"
python labs/week02/query.py "SELECT * FROM attendance WHERE student_id = 'YOUR_ID'"
```

Did you check in on 7 November? Do you have a row in `attendance`, and is it P or A? If the answer surprises you, Part D explains why.

---

## Part D: Investigate the warnings (about 15 minutes)

`query.py` runs SQL on the database that the pipeline built. First, look at the check-ins that match nobody on the roster:

```bash
python labs/week02/query.py "SELECT * FROM unmatched_checkins"
```

Who are these students? Compare them with the newer class list, `roster_v2.csv`:

```bash
python labs/week02/query.py "SELECT r.course, count(*) AS checkins FROM unmatched_checkins AS u LEFT JOIN read_csv('labs/week02/data/export/roster_v2.csv', all_varchar = true) AS r USING (student_id) GROUP BY r.course"
```

Now the second warning. Which check-in has two different IDs?

```bash
python labs/week02/query.py "SELECT checked_in_at, section, typed_id, email_id FROM checkins WHERE typed_id <> email_id"
```

With your partner, explain both problems in one sentence each. The first problem is not the students' fault. Why not? Who could prevent the second one, and how?

---

## Part E: Fix it by re-running, then use the result (about 20 minutes)

Raw data is never edited by hand. Instead, you change the **input** or the **rule** and run the whole pipeline again.

1. Use the newer class list:

```bash
python labs/week02/checkin_pipeline.py --roster v2
```

How many unmatched check-ins are left? Which problem is still there?

2. Take the student ID from the e-mail address, which the form verified, instead of what was typed:

```bash
python labs/week02/checkin_pipeline.py --roster v2 --id-from email
```

Write down the present and absent counts for each section. These match the official attendance list for 7 November.

3. Run exactly the same command **again**. Do the numbers change? Do you get twice as many rows?

```bash
python labs/week02/checkin_pipeline.py --roster v2 --id-from email
python labs/week02/query.py "SELECT count(*) FROM attendance"
```

> **Screenshot 2 for the lab check:** this last run and the count: the summary table, the line `Pipeline finished: run by @<your GitHub name> ...` and the number of rows.

Every step uses `CREATE OR REPLACE`, so running the pipeline twice gives the same result as running it once. Data engineers call this **idempotent**, and it is what makes "fix the input and run it again" safe.

4. Run your two queries from Part C again. What changed for you, and why?

> **Screenshot 3 for the lab check:** your two find-yourself queries with your own student ID, their results and the lines `-- query run by @<your GitHub name> ...`. Not in the data because you joined the course after 7 November? Show the queries and the empty results.

5. Now use what the pipeline served. A pipeline is not finished when the data sits in a database: **serving** hands the result to the people who use it, in a form they can use. The three `[serve]` lines of your last run name the users:

| User | What the pipeline served | Try it |
|---|---|---|
| The teacher | the attendance list `labs/week02/data/output/attendance_2026-11-07.csv` | In the Explorer, open `labs/week02/data/output` and click the file. Find your own row (Ctrl+F). To open it in Excel, right-click the file → **Download**. |
| The department | the summary `labs/week02/data/output/summary_2026-11-07.csv` | Open it the same way: one row per section, with `percent_present`. |
| You | the table `attendance` | Your find-yourself query from step 4. |

With your partner: the teacher and the department never run the pipeline; they only see these files. What would they have believed if the files from your first run in Part C were all they got?

---

## Part F: Spot the undercurrents (about 5 minutes)

The lifecycle stages sit on top of six undercurrents. Match each fact about our check-in to one undercurrent: **security, data management, DataOps, data architecture, orchestration, software engineering**.

| Fact about our check-in | Undercurrent |
|---|---|
| Only students signed in with an `@au.edu` account can submit the check-in form | |
| The roster decides who *should* be in class, and the student ID is the key that links the tables | |
| The `[check]` lines count problems every time the pipeline runs | |
| Google Form → Google Sheet → script was chosen because it is enough for about 100 students | |
| The form closes by itself 60 minutes after it opens, and the pipeline runs after every class | |
| The pipeline is code in Git, so anyone can read it and run it again | |

---

## Part G: Join AWS Academy (about 20 minutes)

Later in the semester some labs run on Amazon Web Services (AWS). AWS Academy gives you two free courses for that. You need no credit card, and nothing is ever charged to you.

| Course | What it is |
|---|---|
| **AWS Academy Data Engineering** | lessons and guided labs made by AWS; each lab has its own **Start Lab** button and timer |
| **AWS Academy Learner Lab** | your own AWS sandbox with a fixed budget, for the labs we design ourselves |

**Join both courses**

1. Open your `@au.edu` mailbox (Outlook). You should have **two** invitations from AWS Academy (sender `notifications@instructure.com`), one for each course. Not there? Look in **Junk**.
2. In the first invitation, click **Get Started**, then **Create My Account**. Choose a password, set the time zone to **Bangkok**, accept the terms and click **Register**. Keep the password safe: you need it all semester. (You already have an AWS Academy account from another course? Log in with it instead.)
3. In the second invitation, click **Get Started** and log in with the same e-mail address and password.
4. Go to https://awsacademy.instructure.com/login/canvas and log in. The **Dashboard** must show both courses. From now on, log in at this address.
5. Open **AWS Academy Data Engineering** → **Modules** and scroll through the list. We will use some of its labs later. You do not need to start any today.

**Start your sandbox once**

6. Open **AWS Academy Learner Lab** → **Modules** → **Launch AWS Academy Learner Lab**. The first time, scroll down and accept the terms (**I agree**).
7. Click **Start Lab**. Wait until the dot next to **AWS** (top left) turns **green**. The first start can take a few minutes.
8. Click **AWS**. The AWS Management Console opens in a new tab. If nothing opens, allow pop-ups for this site.
9. Check the Region at the top right of the console: it should say **N. Virginia** (`us-east-1`). The Learner Lab works only in `us-east-1` and `us-west-2`. Type **S3** in the search bar and open it. Only look: do not create anything today.

> **Screenshot 4 for the lab check:** the AWS console of your Learner Lab, with the Region **N. Virginia** and your account name visible at the top right. Stuck before this step? Take a screenshot of the step where you got stuck instead, and choose the matching answer in question 6.

10. Back on the Learner Lab page, find your **budget** (for example "Used $0 of $50") and the session **timer** at the top.
11. Click **End Lab**.

**Rules for your sandbox (they matter all semester)**

- **The budget cannot be refilled.** If you use all of it, your AWS account is closed and everything in it is deleted. The budget number can lag behind by several hours.
- **End Lab when you finish.** A session also ends by itself when the timer reaches 0 (4 hours); click **Start Lab** again to get more time. End Lab stops virtual machines (EC2), but other services, such as databases, keep running and keep using your budget. So delete what you create at the end of every lab.
- **Do not click Reset** unless the instructor asks you to. It deletes everything in your sandbox.
- Use Chrome or Edge in a normal window. In a private (incognito) window, or with third-party cookies blocked, you get "labs.vocareum.com refused to connect".

No invitation, or stuck at a step? Tell the instructor in class, with your `@au.edu` address. The last question of the lab check asks how far you got. It is not graded.

---

## Challenge (optional)

`sessions.csv` also has `on_time_until`. Change step 5 of `transform()` so that a student who checked in after `on_time_until` gets **L** (late) instead of P. How many L do you get for 7 November? Why?

---

## Before you leave

- [ ] Submit the CSX4211/ITX4211 Lab 2 check in MS Teams: answer the 11 questions and upload Screenshots 1–4. It closes Monday 23 November, 23:59.
- [ ] Learner Lab: click **End Lab** if your sandbox is still running.
- [ ] Stop your codespace: https://github.com/codespaces → **…** → **Stop codespace**.
- [ ] Read for Week 3: *Fundamentals of Data Engineering* (Reis & Housley), chapters 5 and 6.
