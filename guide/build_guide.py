"""Build the student techniques guide. No workshop or personal data is read.

Requires Python 3, numpy, matplotlib and reportlab.
Run: python guide/build_guide.py
"""

from io import BytesIO
from pathlib import Path
import re

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch, Rectangle
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "techniques-guide.pdf"
INK = "#172B4D"
BLUE = "#225EA8"
TEAL = "#087F73"
ORANGE = "#B65A12"
PALE = "#EEF4F8"
WIDTH, HEIGHT = 612, 792
MARGIN = 42
BODY_WIDTH = WIDTH - 2 * MARGIN
COLUMN_WIDTH = 254
plt.rcParams.update({
    "font.size": 10.5,
    "text.parse_math": False,
    "axes.labelsize": 10.5,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "text.color": INK,
    "axes.labelcolor": INK,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def link(label, url):
    return f'<link href="{url}" color="{BLUE}"><u>{label}</u></link>'


PAGES = [
    {
        "title": "Data engineering",
        "question": "How do separate tables become data we can trust?",
        "left": [
            ("The technique", "A <b>join</b> matches rows by a shared key, such as an account ID. "
             "First define the <b>grain</b>: what does one row mean? A usage table can have many "
             "rows per account. An account table should have just one row for that same ID."),
            ("A separate profession", "<b>Data engineers</b> build the pipelines that collect, move, "
             "clean and store data. They keep it fresh, secure and reliable. <b>Data scientists</b> "
             "use data to answer questions, run tests and build models. These are often separate "
             "jobs. Both use Python and SQL, and both check data quality."),
            ("Why this approach emerged", "In 1970, E. F. Codd described the relational model. "
             "It separated the meaning of related tables from their physical storage. Analysts "
             "could ask new questions without redesigning how every record was stored."),
        ],
        "right": [
            ("Where it helps", "A hospital links patient IDs to visits and lab results. A store links "
             "purchases to product details. The shared ID matters more than a name, which may change "
             "or belong to more than one person."),
            ("In Taylor's work and this lab", "Product analytics links usage events to account, "
             "model and plan details. You will combine simulated usage with these tables. Then "
             "you can ask which plans use more tokens or which models people return to."),
            ("Trust the result before plotting", "Check row counts and token totals before and after "
             "a join. A repeated key on both sides can multiply rows and inflate totals. Check "
             "unmatched IDs too. A missing match is not zero usage. If a plan changes over time, "
             "match the plan that was valid when the event happened."),
        ],
        "chart": "join",
        "caption": "Three usage rows stay three rows. The account lookup adds a plan, not more usage.",
        "links": [
            ("Wikipedia: relational model", "https://en.wikipedia.org/wiki/Relational_model"),
            ("pandas merge and validate", "https://pandas.pydata.org/docs/reference/api/pandas.merge.html"),
            ("Codd's original paper (1970)", "https://doi.org/10.1145/362384.362685"),
        ],
    },
    {
        "title": "Pricing and margin",
        "question": "Does a new billing scheme cover the cost of serving users?",
        "left": [
            ("Know which money you mean", "<b>Price</b> is a rate, such as dollars per action. "
             "<b>Revenue</b> is money earned from sales. <b>Cost of goods sold</b> covers the direct "
             "costs of delivering the product. Gross profit is revenue minus those costs. "
             "<b>Gross margin</b> is gross profit divided by revenue, written as a percent."),
            ("Why these measures exist", "A business needs to know more than how much it sold. "
             "A busy service can lose money if each sale costs too much to deliver. Margin "
             "helps compare products with different prices. Markup is different: it divides "
             "profit by cost, not revenue."),
            ("A useful business question", "A video service might sell a monthly plan while paying "
             "for each hour streamed. Heavy viewers can cost much more to serve. For AI products, "
             "model choice, input and output tokens, and cached input affect serving cost."),
        ],
        "right": [
            ("What you will compare", "The notebook models an old-style bill per user action and "
             "a new bill per AI credit (AIC). One action may cause several model calls. Compare "
             "both bills for the <b>same workload</b>, then subtract the modeled hosting cost."),
            ("Read the example below", "Suppose 100 actions use 300 AIC and cost $2.40 to host. "
             "At $0.04 per action, the old bill is $4.00. At $0.01 per AIC, the new bill is $3.00. "
             "Modeled contributions are $1.60 and $0.60. Their margins are 40% and 20%."),
            ("What the lab cannot claim", "These are <b>modeled contribution margins</b>, not actual "
             "gross margins. Actual revenue and other costs are unknown. AIC dollar equivalents "
             "and API list prices are not revenue. Add bills and costs first, then divide; "
             "do not average model-level margins without the right weights."),
        ],
        "chart": "margin",
        "caption": "Modeled contribution margin = (modeled bill - hosting cost) / modeled bill.",
        "links": [
            ("Wikipedia: gross margin", "https://en.wikipedia.org/wiki/Gross_margin"),
            ("Wikipedia: contribution margin", "https://en.wikipedia.org/wiki/Contribution_margin"),
            ("Wikipedia: markup", "https://en.wikipedia.org/wiki/Markup_(business)"),
        ],
    },
    {
        "title": "Survival analysis",
        "question": "How long until an event, even when follow-up is incomplete?",
        "left": [
            ("Why Kaplan-Meier was needed", "In a study, people may join at different times. "
             "The study may end before some have the event. Others may leave early. Throwing "
             "them away wastes evidence. Treating them as event-free forever is also wrong. "
             "Kaplan and Meier's 1958 paper estimates survival from these incomplete records."),
            ("The technique", "Choose an event and a starting point. A <b>Kaplan-Meier curve</b> "
             "starts at 100%. At each event time, multiply the current level by the share of "
             "people still at risk who did not have the event. The curve steps down only "
             "when an event occurs."),
            ("Censored does not mean cured", "A <b>censored</b> person was event-free when we last "
             "saw them. They count as at risk up to that point, then leave the risk set. "
             "Their censoring mark does not make the curve fall."),
        ],
        "right": [
            ("Where it helps: a medical trial", "Compare time to relapse for a treatment group and "
             "a baseline group. A higher curve means more people remain relapse-free. The plot "
             "below uses invented patients. Circles mark relapses; plus signs mark censored follow-up."),
            ("How to read a step", "If survival so far is 80%, and one of five people still at risk "
             "has the event, the next level is 80% x 4/5 = 64%. Late steps may depend on very "
             "few people, so uncertainty usually grows."),
            ("In the workshop", "The event is a subscription spell ending, not a medical outcome. "
             "Some spells are still open when data collection ends. Compare durations while "
             "keeping that partial evidence. The method assumes censoring does not hide a "
             "different event risk within a group. A gap between curves alone does not prove "
             "a treatment or plan caused the difference."),
        ],
        "chart": "survival",
        "caption": "Relapse is the event. Both groups begin with 10 people; '+' is not a relapse.",
        "links": [
            ("Wikipedia: Kaplan-Meier estimator", "https://en.wikipedia.org/wiki/Kaplan%E2%80%93Meier_estimator"),
            ("Original paper (1958)", "https://doi.org/10.1080/01621459.1958.10501452"),
            ("Original paper: university PDF", "https://www.jhanley.biostat.mcgill.ca/c609/material/KaplanMeier.pdf"),
        ],
    },
    {
        "title": "Fraud and abuse",
        "question": "Which patterns deserve a closer look, and what could we get wrong?",
        "left": [
            ("The technique", "Fraud and abuse checks look for patterns that may break rules "
             "or misuse a service. Rules can flag repeated trials on one device. Statistical "
             "models can spot unusual use. A flag is evidence to review, <b>not a verdict</b>."),
            ("Why this field developed", "Banks and online services must review more events than "
             "people can check by hand. Automated screening helps focus human effort. Fraud "
             "research also studies false alarms, changing behavior and cases where the true "
             "outcome is not yet known."),
            ("Where it helps", "A bank may pause a strange card payment and ask the customer to "
             "confirm it. Catching fraud matters, but blocking a valid payment also causes harm. "
             "A useful detector must balance both kinds of error."),
        ],
        "right": [
            ("In the workshop: trial cycling", "You will look for repeated free-trial accounts "
             "linked to a computer. Shared school or family devices can look similar. Check "
             "timing, account overlap and other clues before claiming abuse. One account is "
             "not always one person."),
            ("Understand the trade-off", "In the made-up review below, 50 accounts are flagged. "
             "Only 15 are truly abusive, so <b>precision</b> is 15/50 = 30%. The rule finds "
             "15 of 20 abusive accounts, so <b>recall</b> is 75%. A rule can catch many bad "
             "cases and still create many false alarms."),
            ("What a team could do next", "Use a flag to trigger a review or a small extra check, "
             "not an automatic ban. Track false alarms and appeals. Collect only needed data. "
             "In real work, confirmed outcomes may arrive late; do not treat every unknown "
             "case as honest or abusive."),
        ],
        "chart": "fraud",
        "caption": "Illustrative reviewed outcomes for 1,000 accounts. The notebook does not reveal hidden truth.",
        "links": [
            ("Wikipedia: precision and recall", "https://en.wikipedia.org/wiki/Precision_and_recall"),
            ("Wikipedia: confusion matrix", "https://en.wikipedia.org/wiki/Confusion_matrix"),
            ("Bolton and Hand: research review (2002)", "https://doi.org/10.1214/ss/1042727940"),
        ],
    },
    {
        "title": "Activity metrics",
        "question": "Are people returning often enough to get lasting value?",
        "left": [
            ("Count people, then active days", "<b>DAU</b> counts distinct accounts active on one "
             "day. In a trailing seven-day window, <b>WAU</b> counts accounts active on at least "
             "one day. Here, <b>WEU</b> means at least two days and <b>WDU</b> means at least "
             "five. Repeated actions on one day still count as one active day."),
            ("Why usage logs became useful", "Logs show how people use a service over time. "
             "Cooley and colleagues' 1997 web-mining paper describes finding patterns in "
             "web visits. It is background research, not the origin of DAU or these thresholds. "
             "WEU and WDU here are workshop definitions, not universal standards."),
            ("Read the example", "The grid has four weekly active accounts, three active on "
             "at least two days, and two active on at least five. WDU/WAU = 2/4 = 50%. "
             "DAU on the final day is three."),
        ],
        "right": [
            ("Connect the metric to a decision", "A product team wants people to return because "
             "the tool helps them. If many try it once but few return, test a clearer first "
             "task, a better onboarding lesson or faster results. A game could test a weekly "
             "challenge. Compare repeat use in a fair experiment, not just before and after."),
            ("In the workshop", "Plot activity over time. Compare WDU/WAU across plans (SKUs) "
             "and model groups. This asks what share of weekly users are frequent users. "
             "A higher share may reflect better fit, different users or different work schedules."),
            ("Keep comparisons fair", "Use the same seven-day window and a clear definition of "
             "activity. Count complete windows. A ratio can rise because occasional users "
             "left, so inspect the counts too. More clicks are not always more value; check "
             "task success, satisfaction and cost as well."),
        ],
        "chart": "activity",
        "caption": "Filled squares are active UTC days. The three weekly groups use the same seven days.",
        "links": [
            ("Wikipedia: active users", "https://en.wikipedia.org/wiki/Active_users"),
            ("Cooley et al.: original paper (1997)", "https://dmr.cs.umn.edu/Papers/P1997_5.pdf"),
            ("IEEE publication record", "https://ieeexplore.ieee.org/document/632303"),
        ],
    },
    {
        "title": "Market baskets",
        "question": "What goes together, and could that pattern guide a useful offer?",
        "left": [
            ("Start with a store", "A grocery store wants shoppers to spend more. It studies "
             "which items appear together, then considers a chips-and-salsa combo sale. "
             "An <b>association rule</b> describes a pattern: shoppers buying chips often "
             "also buy salsa. It does not show that chips caused the salsa purchase."),
            ("Three measures, one example", "Of 100 baskets, 40 contain chips, 30 contain salsa "
             "and 24 contain both. <b>Support</b> is the share with both: 24%. "
             "<b>Confidence</b> is the share of chips baskets with salsa: 24/40 = 60%. "
             "<b>Lift</b> compares that with salsa's usual 30% rate: 60%/30% = 2."),
            ("Why the method emerged", "Agrawal, Imielinski and Swami's 1993 paper described "
             "mining purchase records for association rules. Computers could search huge "
             "numbers of item pairs that a store could not check by hand."),
        ],
        "right": [
            ("Turn the pattern into a test", "Lift of 2 means chips baskets are twice as likely "
             "to contain salsa as baskets overall. Test a combo offer with a random group "
             "of shoppers. Compare spending and profit with a group without the offer. "
             "A discount might replace full-price sales rather than add new sales."),
            ("From groceries to AI models", "An account's weekly basket is the set of models "
             "it uses. You will compare two weeks: are baskets larger, and do people stay "
             "with one provider? This is a simple basket comparison, not a full rule-mining task."),
            ("An activity example of lift", "Imagine 200 eligible accounts. In week 1, 50 use "
             "model X. In week 2, 30 of those 50 are active on five days, versus 80 of all "
             "200. Activity lift is (30/50)/(80/200) = 1.5. This uses a later outcome, not "
             "co-purchase. It suggests a question to test, not proof that model X builds a habit."),
        ],
        "chart": "baskets",
        "caption": "Chips-and-salsa lift is 2. The chance is 60% rather than 30%, not a 2-point increase.",
        "links": [
            ("Wikipedia: association rule learning", "https://en.wikipedia.org/wiki/Association_rule_learning"),
            ("Wikipedia: lift", "https://en.wikipedia.org/wiki/Lift_(data_mining)"),
            ("Agrawal et al.: original paper (1993)", "https://doi.org/10.1145/170035.170072"),
        ],
    },
    {
        "title": "Switching and Sankey diagrams",
        "question": "After a launch, where do users move, and who stays?",
        "left": [
            ("The technique", "A <b>Sankey diagram</b> shows flows with bands. A wider band "
             "means more people, energy or money follows that path. For switching, each "
             "account has one starting group and one ending group. The flows must add "
             "up to the group totals."),
            ("The original steam-engine problem", "In an 1898 report, Kennedy and Sankey used "
             "a flow diagram to show useful energy and wasted heat in a steam engine. "
             "The aim was to understand efficiency, not customer choice. The diagram type "
             "is named for Sankey, but proportional flow maps existed earlier."),
            ("Where it helps today", "Energy planners trace power from fuel to useful output. "
             "A product team can trace users from one model to another. Unlike two separate "
             "bar charts, the bands show the actual paths between the groups."),
        ],
        "right": [
            ("In the workshop", "Choose a week before and a week after a model launch. Give "
             "each account a top model using its token total for that week. Draw the flows "
             "between top models. Then compare switching by provider or subscription plan."),
            ("Read the example", "Of 100 matched accounts, 40 move to the new model. Ten "
             "switch between A and B. The other 50 keep their top model. A and B both "
             "send users to the new model, which a totals-only chart would hide."),
            ("Ask a sharper question", "Are users loyal to one model or just one provider? "
             "Do plan limits change who can switch? Fix a rule for ties. Accounts missing "
             "from one week may be inactive or new; do not call them switchers by mistake. "
             "A launch and a change happening together do not by themselves prove cause."),
        ],
        "chart": "sankey",
        "caption": "Each band counts accounts, not tokens. Left and right each sum to 100.",
        "links": [
            ("Wikipedia: Sankey diagram", "https://en.wikipedia.org/wiki/Sankey_diagram"),
            ("Original 1898 report: archive", "https://zenodo.org/records/2036163"),
            ("Original report DOI", "https://doi.org/10.1680/imotp.1898.19100"),
            ("View Sankey's 1898 diagram", "https://commons.wikimedia.org/wiki/File:JIE_Sankey_V5_Fig1.png"),
        ],
    },
    {
        "title": "Bayesian launch forecasting",
        "question": "How can an earlier launch help us make a forecast that improves?",
        "left": [
            ("Start with what you know", "Before a new model launches, we do not know how much "
             "people will use it. A past launch gives a starting guess. A <b>prior</b> is "
             "a range of plausible values, not a fact. Its width says how unsure we are. "
             "<b>Standard deviation (SD)</b> is a measure of that spread."),
            ("Then learn from new data", "Observe the new launch's first few days. A "
             "<b>likelihood</b> says how well each possible value fits those observations. "
             "Combine it with the prior to get a <b>posterior</b>: the updated range. "
             "More useful evidence can move the center and narrow the range."),
            ("Why this idea matters", "Bayes studied how to learn an unknown chance from "
             "evidence. Richard Price presented his essay in 1763, after Bayes died. "
             "Today the same idea helps update demand, weather and risk forecasts "
             "rather than treating a first guess as fixed."),
        ],
        "right": [
            ("A small launch example", "Suppose the prior average is 1,000 tokens per active "
             "account per day. New daily values are 1,200, 1,500 and 1,200. With the simple "
             "noise assumptions below, the updated average is 1,225. With 200 active "
             "accounts, that implies 245,000 tokens per day."),
            ("What you will see in the notebook", "The demo aligns two fictional launches by "
             "days since launch. It uses the older launch as a prior and the first three "
             "days of the newer launch as evidence. Run the provided code; there is no "
             "blank to fill. Change the number of early days and see how the forecast moves."),
            ("Read the uncertainty correctly", "The shaded range describes the <b>unknown average</b>. "
             "Actual daily use varies more. The forecast also assumes a fixed active-account "
             "count. A different audience, price or rollout can break those assumptions. "
             "Never use future days to train a forecast for those same days."),
        ],
        "chart": "bayes",
        "caption": "Illustration: prior SD = 300; daily noise SD = 300; three new days. Posterior SD = 150.",
        "links": [
            ("Wikipedia: Bayesian inference", "https://en.wikipedia.org/wiki/Bayesian_inference"),
            ("Wikipedia: credible interval", "https://en.wikipedia.org/wiki/Credible_interval"),
            ("Bayes and Price: original essay (1763)", "https://doi.org/10.1098/rstl.1763.0053"),
        ],
    },
    {
        "title": "Enterprise analysis",
        "question": "Why might individuals and businesses adopt the same tool differently?",
        "left": [
            ("Different units, different choices", "An individual may try a model today and "
             "change plans tomorrow. A business may need budget approval, a security review "
             "and staff training first. It may buy seats for people who have not started "
             "using the tool yet. A customer company is not the same unit as an active user."),
            ("The technique", "Group data by business, plan or cohort, then compare totals "
             "and rates. A <b>cohort</b> is a group with a shared starting point, such as "
             "the month of signup. Separate reach, repeat use, cost and timing instead "
             "of reducing every business to one large token total."),
            ("Why it helps decisions", "A software team might use a quick signup flow for "
             "individuals but a staged rollout and training for a company. Luhn's 1958 "
             "business-intelligence paper described getting useful information to the "
             "parts of an organization that need it."),
        ],
        "right": [
            ("In the workshop", "Compare business usage, work schedules and model choices. "
             "A weekday pattern can differ from personal use on weekends. Large teams may "
             "adopt in waves. Treat these as ideas to investigate, not rules that every "
             "company or individual follows."),
            ("Choose whose experience to average", "Suppose a small firm has 6 frequent users "
             "out of 10, and a large firm has 18 out of 90. Across accounts, the share is "
             "24/100 = 24%. If each company gets equal weight, the mean is "
             "(60% + 20%)/2 = 40%. Both are correct; they answer different questions."),
            ("What to compare fairly", "Use the same time window and account status. Show "
             "group sizes beside rates. A paid seat, a weekly active account and a frequent "
             "user are different counts. Do not compare a company's total use with one "
             "person's use and call the difference better engagement."),
        ],
        "chart": "enterprise",
        "caption": "Left: a possible schedule pattern. Right: the same two firms, with two weighting choices.",
        "links": [
            ("Wikipedia: cohort analysis", "https://en.wikipedia.org/wiki/Cohort_analysis"),
            ("Wikipedia: weighted arithmetic mean", "https://en.wikipedia.org/wiki/Weighted_arithmetic_mean"),
            ("Luhn: original BI paper (1958)", "https://doi.org/10.1147/rd.24.0314"),
        ],
    },
    {
        "title": "Cache incident detection",
        "question": "When does an unusual cache drop need a closer look?",
        "left": [
            ("The technique", "A cache stores input that can be reused. A <b>cache-read "
             "rate</b> is cached input tokens divided by all input tokens. Compare the rate "
             "over time for each provider. A sudden drop may be an incident, but it can "
             "also reflect a different mix of models or tasks."),
            ("Why teams monitor", "Control charts help teams notice when a process moves "
             "away from its usual pattern. They do not prove why it changed. A useful "
             "alert should focus attention without sending people too many false alarms."),
            ("Count tokens, not percentages", "Add cache-read tokens and input tokens in "
             "each time period first. Then divide the sums. Averaging row percentages "
             "gives a tiny request the same weight as a huge request."),
        ],
        "right": [
            ("A cost example", "For one million input tokens, suppose cached reads cost "
             "$0.10 per million and ordinary input costs $1.00. With no cache writes, "
             "a 90% read rate costs $0.19. At 70%, it costs $0.37: an extra $0.18 "
             "for the same input. Actual costs depend on the price keys and hosts."),
            ("In the workshop", "Compare time periods and providers, then inspect a drop "
             "against a baseline. Find which models contributed. A provider-wide rate can "
             "move when the model mix changes, even if each model's own rate does not."),
            ("Before calling an incident", "Check time zones, missing data and token volume. "
             "Small buckets can move a lot by chance. Compare similar traffic and look "
             "for supporting evidence. A flag starts an investigation, not a verdict."),
        ],
        "chart": "incident",
        "caption": "Example: a lower cache-read share can raise cost for the same input tokens.",
        "links": [
            ("Wikipedia: control chart", "https://en.wikipedia.org/wiki/Control_chart"),
            ("NIST: control charts", "https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc3.htm"),
            ("pandas: groupby", "https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.groupby.html"),
        ],
    },
    {
        "title": "Cost concentration",
        "question": "How unevenly is cost distributed across accounts?",
        "left": [
            ("The technique", "Sort accounts from lowest to highest cost. A <b>Lorenz "
             "curve</b> plots the cumulative share of total cost against the cumulative "
             "share of accounts. The diagonal shows equal cost per account. A curve "
             "farther below it means cost is more concentrated."),
            ("Why it emerged", "Max Lorenz introduced the curve in 1905 to study the "
             "distribution of wealth. It can describe many quantities today, including "
             "spending and usage cost. Its shape shows inequality, not its cause."),
            ("A simple example", "Four accounts cost $1, $1, $2 and $6. The lowest half "
             "of accounts accounts for $2 of the $10 total, or 20%. The highest-cost "
             "account alone accounts for 60%."),
        ],
        "right": [
            ("In the workshop", "Choose one plan and month. Sum modeled hosting cost "
             "per account and sort the accounts. Plot cumulative user share and "
             "cumulative cost share. Make sure both axes go from 0% to 100%."),
            ("A second view", "A percentile plot can show each account's dollar cost "
             "against its position in the sorted accounts. Dollars per account are not "
             "the cumulative share of dollars. Both views help, but answer different "
             "questions."),
            ("Interpret carefully", "Say which accounts qualify, including how you treat "
             "accounts without usage. Show the plan and month. A concentrated cost does "
             "not prove a user caused a problem or that an intervention will work. "
             "Actual customer revenue is not in this data."),
        ],
        "chart": "concentration",
        "caption": "Four invented accounts: the lowest 50% account for 20% of total cost.",
        "links": [
            ("Wikipedia: Lorenz curve", "https://en.wikipedia.org/wiki/Lorenz_curve"),
            ("Lorenz: original paper (1905)", "https://doi.org/10.2307/2276207"),
            ("CORE Econ: Lorenz curves", "https://books.core-econ.org/doing-economics/book/text/05-02.html"),
        ],
    },
]


BODY = ParagraphStyle("body", fontName="Helvetica", fontSize=10.4,
                      leading=13.3, textColor=colors.HexColor(INK))
HEADING = ParagraphStyle("heading", parent=BODY, fontName="Helvetica-Bold",
                         fontSize=11.2, leading=14, textColor=colors.HexColor(TEAL))
SMALL = ParagraphStyle("small", parent=BODY, fontSize=9.4, leading=12)


def paragraph(c, text, x, top, width, style=BODY):
    p = Paragraph(text, style)
    _, height = p.wrap(width, HEIGHT)
    p.drawOn(c, x, top - height)
    return top - height


def chart_base(ax):
    ax.set_facecolor("white")
    ax.grid(axis="y", alpha=0.15)
    ax.set_axisbelow(True)


def table(ax, rows, widths, position=(0, 0, 1, 1)):
    ax.axis("off")
    t = ax.table(cellText=rows, colWidths=widths, cellLoc="center", bbox=position)
    t.auto_set_font_size(False)
    t.set_fontsize(11)
    for (row, _), cell in t.get_celld().items():
        cell.set_edgecolor("#C9D6DF")
        if row == 0:
            cell.set_facecolor(PALE)
            cell.set_text_props(weight="bold", color=INK)
    return t


def km_curve(times, observed):
    times, observed = np.asarray(times), np.asarray(observed, dtype=bool)
    x, y = [0.0], [1.0]
    deaths, censored = [], []
    survival = 1.0
    for time in np.unique(times):
        risk = int((times >= time).sum())
        events = int(((times == time) & observed).sum())
        survival *= 1 - events / risk
        x.append(float(time))
        y.append(survival)
        if events:
            deaths.append((float(time), survival))
        if ((times == time) & ~observed).any():
            censored.append((float(time), survival))
    return x, y, deaths, censored


def ribbon(ax, x0, x1, y0, y1, width, color):
    mid = (x0 + x1) / 2
    points = [(x0, y0), (mid, y0), (mid, y1), (x1, y1),
              (x1, y1 + width), (mid, y1 + width),
              (mid, y0 + width), (x0, y0 + width), (x0, y0)]
    codes = [MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
             MplPath.LINETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
             MplPath.CLOSEPOLY]
    ax.add_patch(PathPatch(MplPath(points, codes), facecolor=color,
                           alpha=0.5, edgecolor="white", linewidth=0.4))


def make_chart(kind):
    fig = plt.figure(figsize=(7.3, 2.6), facecolor="white")
    if kind == "join":
        axes = [fig.add_axes(rect) for rect in [
            [.01, .20, .22, .62], [.31, .30, .22, .46], [.64, .20, .35, .62]]]
        table(axes[0], [["ID", "Tokens"], ["u1", "6"], ["u1", "4"], ["u2", "5"]], [.45, .55])
        table(axes[1], [["ID", "Plan"], ["u1", "Pro"], ["u2", "Free"]], [.45, .55])
        table(axes[2], [["ID", "Tokens", "Plan"], ["u1", "6", "Pro"],
                        ["u1", "4", "Pro"], ["u2", "5", "Free"]], [.3, .35, .35])
        for x, name in [(0.12, "Usage"), (.42, "Accounts"), (.815, "Joined")]:
            fig.text(x, .92, name, ha="center", weight="bold", fontsize=11)
        fig.text(.27, .50, "+", ha="center", fontsize=20, color=TEAL)
        fig.text(.585, .50, "=", ha="center", fontsize=20, color=TEAL)
        fig.text(.5, .04, "Total tokens before = 15       Total tokens after = 15",
                 ha="center", fontsize=11)
    elif kind == "margin":
        ax = fig.add_axes([.09, .19, .45, .72])
        bills = np.array([4.0, 3.0])
        cost = np.array([2.4, 2.4])
        ax.bar(["Old: action", "New: AIC"], cost, color=BLUE, label="Hosting cost")
        ax.bar(["Old: action", "New: AIC"], bills - cost, bottom=cost,
               color=TEAL, label="Contribution")
        for i, bill in enumerate(bills):
            ax.text(i, bill + .08, f"${bill:.2f}", ha="center", weight="bold")
        ax.set_ylim(0, 4.7)
        ax.set_ylabel("Dollars for the same workload")
        chart_base(ax)
        fig.text(.62, .83, "Old bill: 100 x $0.04 = $4.00", fontsize=11)
        fig.text(.62, .66, "New bill: 300 x $0.01 = $3.00", fontsize=11)
        fig.text(.62, .45, "Old margin: $1.60 / $4 = 40%", fontsize=11, color=TEAL)
        fig.text(.62, .28, "New margin: $0.60 / $3 = 20%", fontsize=11, color=TEAL)
        fig.legend(handles=[Rectangle((0, 0), 1, 1, color=BLUE),
                            Rectangle((0, 0), 1, 1, color=TEAL)],
                   labels=["Hosting cost", "Modeled contribution"], loc="lower center",
                   ncol=2, frameon=False, bbox_to_anchor=(.5, -.03))
    elif kind == "survival":
        ax = fig.add_axes([.10, .28, .86, .63])
        groups = [
            ("Baseline", BLUE, [1, 2, 3, 4, 5, 6, 6, 7, 8, 8],
             [1, 1, 1, 0, 1, 1, 0, 1, 0, 0]),
            ("Treatment", TEAL, [2, 3, 4, 5, 6, 6, 7, 8, 8, 8],
             [1, 0, 1, 0, 1, 0, 0, 1, 0, 0]),
        ]
        for name, color, times, events in groups:
            x, y, deaths, censored = km_curve(times, events)
            ax.step(x, y, where="post", label=name, color=color, linewidth=2)
            if deaths:
                ax.scatter(*zip(*deaths), marker="o", s=23, color=color, zorder=3)
            if censored:
                ax.scatter(*zip(*censored), marker="+", s=70, color=color, zorder=4)
        ax.set(xlim=(0, 8.3), ylim=(0, 1.06), xlabel="Months since study entry",
               ylabel="Share relapse-free")
        ax.set_yticks([0, .25, .5, .75, 1], ["0%", "25%", "50%", "75%", "100%"])
        chart_base(ax)
        handles, labels = ax.get_legend_handles_labels()
        handles += [Line2D([], [], color=INK, marker="o", linestyle="None"),
                    Line2D([], [], color=INK, marker="+", linestyle="None", markersize=9)]
        labels += ["Relapse event", "Censored"]
        fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False,
                   bbox_to_anchor=(.51, -.035))
    elif kind == "fraud":
        ax = fig.add_axes([.02, .10, .64, .79])
        table(ax, [["", "Abuse", "Valid use"], ["Flagged", "15", "35"],
                   ["Not flagged", "5", "945"]], [.4, .3, .3])
        fig.text(.4, .96, "Confirmed outcome", ha="center", weight="bold", fontsize=11)
        fig.text(.72, .76, "Precision", color=TEAL, fontsize=11, weight="bold")
        fig.text(.72, .62, "15 / 50 = 30%", fontsize=12)
        fig.text(.72, .39, "Recall", color=TEAL, fontsize=11, weight="bold")
        fig.text(.72, .25, "15 / 20 = 75%", fontsize=12)
    elif kind == "activity":
        grid = np.array([[1] * 7, [1, 1, 1, 1, 0, 0, 1],
                         [0, 0, 1, 0, 0, 0, 1], [0, 1, 0, 0, 0, 0, 0], [0] * 7])
        assert (grid.sum(axis=1) >= 1).sum() == 4
        assert (grid.sum(axis=1) >= 2).sum() == 3
        assert (grid.sum(axis=1) >= 5).sum() == 2
        assert grid[:, -1].sum() == 3
        ax = fig.add_axes([.08, .20, .59, .70])
        for row in range(5):
            for col in range(7):
                ax.add_patch(Rectangle((col, row), .88, .83, facecolor=TEAL if grid[row, col] else PALE,
                                       edgecolor="white"))
        ax.set(xlim=(-.05, 7), ylim=(5, -.15))
        ax.set_xticks(np.arange(7) + .44, ["M", "T", "W", "T", "F", "S", "S"])
        ax.set_yticks(np.arange(5) + .4, ["A", "B", "C", "D", "E"])
        ax.set_ylabel("Account")
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.tick_params(length=0)
        fig.text(.73, .80, "WAU = 4", fontsize=12)
        fig.text(.73, .61, "WEU = 3", fontsize=12)
        fig.text(.73, .42, "WDU = 2", fontsize=12)
        fig.text(.73, .20, "WDU / WAU = 50%", fontsize=11, weight="bold", color=TEAL)
        fig.text(.35, .03, "Each column is one UTC day", ha="center", fontsize=10)
    elif kind == "baskets":
        ax = fig.add_axes([.02, .14, .53, .69])
        table(ax, [["100 baskets", "Salsa", "No salsa"], ["Chips", "24", "16"],
                   ["No chips", "6", "54"]], [.4, .3, .3])
        fig.text(.63, .80, "Support = 24 / 100 = 24%", fontsize=11)
        fig.text(.63, .58, "Confidence = 24 / 40 = 60%", fontsize=11)
        fig.text(.63, .36, "Usual salsa rate = 30 / 100", fontsize=11)
        fig.text(.63, .14, "Lift = 60% / 30% = 2", fontsize=12, weight="bold", color=TEAL)
    elif kind == "sankey":
        ax = fig.add_axes([.02, .02, .96, .91])
        ax.axis("off")
        ax.set(xlim=(0, 1), ylim=(0, 1))
        scale = .006
        left = {"A": .51, "B": .12}
        right = {"A": .66, "B": .42, "New": .10}
        left_pos, right_pos = left.copy(), right.copy()
        flows = [("A", "A", 35), ("A", "B", 5), ("A", "New", 20),
                 ("B", "A", 5), ("B", "B", 15), ("B", "New", 20)]
        palette = {"A": BLUE, "B": TEAL, "New": ORANGE}
        for source, target, count in flows:
            ribbon(ax, .19, .80, left_pos[source], right_pos[target], count * scale, palette[source])
            left_pos[source] += count * scale
            right_pos[target] += count * scale
        for name, count in [("A", 60), ("B", 40)]:
            ax.add_patch(Rectangle((.15, left[name]), .04, count * scale, color=palette[name]))
            ax.text(.13, left[name] + count * scale / 2, f"{name}: {count}", ha="right", va="center")
        for name, count in [("A", 40), ("B", 20), ("New", 40)]:
            ax.add_patch(Rectangle((.80, right[name]), .04, count * scale, color=palette[name]))
            ax.text(.86, right[name] + count * scale / 2, f"{name}: {count}", va="center")
        ax.text(.17, .98, "Week 1", ha="center", weight="bold")
        ax.text(.82, .98, "Week 2", ha="center", weight="bold")
    elif kind == "bayes":
        ax = fig.add_axes([.10, .28, .86, .64])
        x = np.linspace(0, 2200, 600)
        mu0, sd0, noise = 1000, 300, 300
        samples = np.array([1200, 1500, 1200])
        var = 1 / (1 / sd0**2 + len(samples) / noise**2)
        mu = var * (mu0 / sd0**2 + samples.sum() / noise**2)
        sd = np.sqrt(var)
        assert np.isclose(mu, 1225) and np.isclose(sd, 150)
        normal = lambda mean, std: np.exp(-.5 * ((x - mean) / std)**2) / (std * np.sqrt(2 * np.pi))
        prior, posterior = normal(mu0, sd0), normal(mu, sd)
        ax.plot(x, prior, color=BLUE, linewidth=2, label="Prior: 1,000")
        ax.plot(x, posterior, color=TEAL, linewidth=2, label="Updated: 1,225")
        ax.fill_between(x, 0, posterior, where=(x >= mu - 1.96 * sd) & (x <= mu + 1.96 * sd),
                        color=TEAL, alpha=.19, label="95% range for mean")
        ax.set(xlabel="Mean tokens per active account per day", ylabel="Plausibility")
        ax.set_yticks([])
        ax.legend(frameon=False, loc="upper left")
        fig.text(.57, .025, "Updated 95% range: about 931 to 1,519", ha="center", fontsize=10)
    elif kind == "enterprise":
        ax = fig.add_axes([.09, .23, .48, .67])
        ax.plot(range(7), [60, 65, 66, 64, 62, 18, 12], "o-", color=BLUE, label="Business")
        ax.plot(range(7), [40, 43, 41, 42, 45, 56, 54], "s-", color=TEAL, label="Individual")
        ax.set_xticks(range(7), ["M", "T", "W", "T", "F", "S", "S"])
        ax.set(ylabel="Daily active share (%)", ylim=(0, 80))
        ax.legend(frameon=False, loc="lower left")
        chart_base(ax)
        bx = fig.add_axes([.72, .23, .26, .67])
        bx.bar(["Accounts", "Firms"], [24, 40], color=[BLUE, TEAL], width=.6)
        bx.set(ylim=(0, 55), ylabel="Frequent-user share (%)")
        for i, value in enumerate([24, 40]):
            bx.text(i, value + 2, f"{value}%", ha="center", weight="bold")
        fig.text(.85, .96, "Equal weight for...", ha="center", fontsize=10)
        chart_base(bx)
    elif kind == "incident":
        ax = fig.add_axes([.09, .25, .48, .65])
        ax.plot([1, 2, 3, 4], [90, 90, 70, 90], "o-", color=BLUE, linewidth=2)
        ax.set(ylim=(50, 100), xticks=[1, 2, 3, 4], xlabel="Time period",
               ylabel="Cache-read share (%)")
        chart_base(ax)
        fig.text(.64, .78, "90% cached: $0.19", fontsize=12)
        fig.text(.64, .55, "70% cached: $0.37", fontsize=12)
        fig.text(.64, .30, "Extra cost: $0.18", fontsize=12, weight="bold", color=ORANGE)
    elif kind == "concentration":
        ax = fig.add_axes([.11, .26, .48, .66])
        ax.plot([0, 100], [0, 100], "--", color=INK, label="Equal cost")
        ax.plot([0, 25, 50, 75, 100], [0, 10, 20, 40, 100],
                "o-", color=TEAL, label="Actual cost")
        ax.set(xlim=(0, 100), ylim=(0, 100), xlabel="Cumulative accounts (%)",
               ylabel="Cumulative cost (%)")
        ax.legend(frameon=False, loc="upper left")
        chart_base(ax)
        fig.text(.68, .75, "Costs: $1, $1, $2, $6", fontsize=11)
        fig.text(.68, .52, "Lowest 50%: $2", fontsize=11)
        fig.text(.68, .30, "Share: $2 / $10 = 20%", fontsize=11, color=TEAL, weight="bold")
    else:
        raise ValueError(f"Unknown chart: {kind}")
    output = BytesIO()
    fig.savefig(output, format="png", dpi=180, facecolor="white")
    plt.close(fig)
    output.seek(0)
    return output


def footer(c, page_number):
    c.setStrokeColor(colors.HexColor("#CFDCE5"))
    c.line(MARGIN, 30, WIDTH - MARGIN, 30)
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor(INK))
    c.drawString(MARGIN, 17, "AI product analytics workshop  |  All figures use illustrative, made-up data.")
    c.drawRightString(WIDTH - MARGIN, 17, str(page_number))


def cover(c):
    c.setFillColor(colors.HexColor(INK))
    c.setFont("Helvetica-Bold", 32)
    c.drawString(MARGIN, 726, "Data science techniques")
    c.setFont("Helvetica", 17)
    c.setFillColor(colors.HexColor(TEAL))
    c.drawString(MARGIN, 694, "A field guide for your workshop")
    y = paragraph(c, "Start with a question. Learn the idea. Read the picture. Then try the "
                  "matching notebook section. You do not need to master every method today.",
                  MARGIN, 661, BODY_WIDTH)
    y = paragraph(c, "<b>The setting:</b> a fictional AI coding product. Accounts use different "
                  "models, choose plans and sometimes leave. You will turn those records into "
                  "evidence that a product team could use.", MARGIN, y - 14, BODY_WIDTH)
    y -= 30
    for i, page in enumerate(PAGES, start=1):
        c.setFillColor(colors.HexColor(PALE if i % 2 else "#F7FAFC"))
        c.roundRect(MARGIN, y - 28, BODY_WIDTH, 36, 5, stroke=0, fill=1)
        c.setFillColor(colors.HexColor(TEAL))
        c.setFont("Helvetica-Bold", 12)
        c.drawString(MARGIN + 12, y - 8, f"{i:02d}")
        c.setFillColor(colors.HexColor(INK))
        c.setFont("Helvetica-Bold", 11.5)
        c.drawString(MARGIN + 46, y - 5, page["title"])
        c.setFont("Helvetica", 10)
        c.drawString(MARGIN + 46, y - 21, page["question"])
        y -= 40
    y = paragraph(c, "<b>Use the links:</b> each topic ends with clickable terms, tutorials or "
                  "original research. Some publisher pages may require access; open archive "
                  "links are included where available.", MARGIN, y - 8, BODY_WIDTH)
    paragraph(c, "<b>Keep evidence honest:</b> the workshop's people, activity and launch stories "
              "are synthetic. Some model names and pricing references come from public sources. "
              "The examples here are illustrations, not exercise answers. The last pages "
              "explain the notebook's fields.",
              MARGIN, y - 12, BODY_WIDTH)
    footer(c, 1)
    c.showPage()


def topic_page(c, page, number):
    c.setFillColor(colors.HexColor(TEAL))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(MARGIN, 752, f"WORKSHOP FIELD GUIDE  /  SECTION {number:02d}")
    c.setFillColor(colors.HexColor(INK))
    c.setFont("Helvetica-Bold", 23)
    c.drawString(MARGIN, 718, page["title"])
    c.setFont("Helvetica", 11)
    c.drawString(MARGIN, 696, page["question"])
    for side, x in [("left", MARGIN), ("right", MARGIN + COLUMN_WIDTH + 20)]:
        y = 670
        for heading, content in page[side]:
            y = paragraph(c, heading, x, y, COLUMN_WIDTH, HEADING)
            y = paragraph(c, content, x, y - 4, COLUMN_WIDTH)
            y -= 12
        if y < 338:
            raise ValueError(f"Text overlaps the visual: {page['title']} {side}, bottom={y:.1f}")
    c.setFillColor(colors.HexColor(TEAL))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(MARGIN, 321, "VISUAL EXAMPLE")
    c.setFillColor(colors.HexColor(INK))
    c.setFont("Helvetica", 9.5)
    c.drawRightString(WIDTH - MARGIN, 321, "Illustrative data")
    c.drawImage(ImageReader(make_chart(page["chart"])), MARGIN, 122,
                width=BODY_WIDTH, height=188, mask="auto")
    bottom = paragraph(c, page["caption"], MARGIN, 116, BODY_WIDTH, SMALL)
    if bottom < 86:
        raise ValueError(f"Caption is too long: {page['title']}")
    links = "  |  ".join(link(label, url) for label, url in page["links"])
    bottom = paragraph(c, "<b>Explore:</b> " + links, MARGIN, 77, BODY_WIDTH, SMALL)
    if bottom < 34:
        raise ValueError(f"Sources overlap footer: {page['title']}")
    footer(c, number + 1)
    c.showPage()


def plain_text(page):
    content = " ".join(text for side in ["left", "right"] for _, text in page[side])
    return re.sub("<[^>]+>", "", content)


DICTIONARY = [
    {
        "title": "Data dictionary: analysis",
        "intro": "The notebook's compact working table is called analysis. One row is one "
                 "six-hour usage aggregate for an account, model, route, host and price "
                 "key, among other grouping fields. Multiple rows can share account and time.",
        "left": [
            ("user_id", "Text account ID. Join key to users and subscriptions; one account "
             "may have many usage or subscription rows."),
            ("time", "UTC text timestamp for the start of the six-hour usage bucket. "
             "Convert to a datetime before filtering or grouping by day."),
            ("region", "Text region of the account, joined from users."),
            ("user_type", "Text subscription plan or SKU recorded for this usage."),
            ("model_name", "Text name of the model that actually handled the calls."),
            ("provider", "Text model provider, such as a model's company."),
            ("primary_provider", "Text declared provider preference from users. It need "
             "not match the provider of every actual call."),
        ],
        "right": [
            ("model_call_count", "Whole number of model calls in this usage aggregate. "
             "One user request can trigger several calls."),
            ("user_request_count", "Whole number of admitted user requests, also called "
             "turns, attributed to this aggregate. Count turns, not calls, for the "
             "old-style per-turn bill."),
            ("total_input_tokens", "Whole number of input text tokens. Includes cached "
             "reads and uncached input."),
            ("aic", "Numeric AI credits consumed. An AIC dollar proxy is not revenue."),
            ("hosting_cost_usd", "Numeric modeled provider hosting cost in US dollars. "
             "It is not the customer's bill."),
            ("business_id", "Text business ID, or missing for an individual account. "
             "Join to businesses on business_id when studying firms."),
        ],
    },
    {
        "title": "Data dictionary: extra fields",
        "intro": "Some sections use a small selection from the raw tables. Times are UTC. "
                 "IDs and price keys are text; counts and token amounts are whole numbers.",
        "left": [
            ("Requests and calls", "user_requests has one row per user action. "
             "user_request_id joins to model_requests, which has one row per model call; "
             "request_id identifies that call. status shows admitted or blocked. "
             "Retries and extra calls are not extra turns."),
            ("Token components", "cache_read_tokens are reused input tokens. "
             "cache_write_tokens are a subset of uncached input. "
             "ordinary_billed_input_tokens exclude writes. output_tokens count generated "
             "text. Do not count writes twice."),
            ("Price keys and rates", "api_price_key and copilot_price_key match price_key "
             "in their respective price tables. input_rate, cache_read_rate, "
             "cache_write_rate and output_rate are USD per million tokens."),
            ("bucket and incident_cost", "bucket groups provider and UTC time. "
             "input_tokens, read_tokens and ordinary_tokens are token counts; "
             "observed_hosting_usd is modeled USD. read_rate and baseline_rate "
             "are fractions, drop is their difference, and flag is true or false. "
             "incident_cost adds estimated_saving_usd: hypothetical savings in USD."),
        ],
        "right": [
            ("Cache investigation", "Use usage time, provider, host, price key, token "
             "components and hosting_cost_usd. Add read tokens and input tokens before "
             "dividing; the result is a share, not a dollar cost."),
            ("Subscriptions", "subscriptions contains user_id, sku, valid_from and "
             "valid_to. Each row is one plan interval. It includes valid_from and excludes "
             "valid_to. Match account and time when finding an eligible plan."),
            ("Cost concentration", "For a selected plan and month, combine eligible "
             "subscriptions with usage time, user_type, user_id and hosting_cost_usd. "
             "Include eligible zero-usage accounts where the exercise asks for them."),
            ("cost_accounts", "One row per eligible account. user_id is its account key; "
             "cost_usd is modeled hosting dollars. user_share and cost_share are "
             "cumulative fractions, not dollars per account."),
            ("More detail", "The complete " + link("student schema", "https://github.com/tbogoodnews/ai-product-usage-data-science-lab-students/blob/main/schema.md")
             + " describes every table and its units. Public model names and price "
             "references are not simulated customer records."),
        ],
    },
]


def dictionary_page(c, page, number):
    c.setFillColor(colors.HexColor(TEAL))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(MARGIN, 752, "WORKSHOP FIELD GUIDE  /  DATA DICTIONARY")
    c.setFillColor(colors.HexColor(INK))
    c.setFont("Helvetica-Bold", 21)
    c.drawString(MARGIN, 718, page["title"])
    top = paragraph(c, page["intro"], MARGIN, 691, BODY_WIDTH)
    for side, x in [("left", MARGIN), ("right", MARGIN + COLUMN_WIDTH + 20)]:
        y = top - 20
        for heading, content in page[side]:
            y = paragraph(c, heading, x, y, COLUMN_WIDTH, HEADING)
            y = paragraph(c, content, x, y - 3, COLUMN_WIDTH)
            y -= 10
        if y < 46:
            raise ValueError(f"Dictionary overlaps footer: {page['title']} {side}, bottom={y:.1f}")
    footer(c, number)
    c.showPage()


def main():
    c = canvas.Canvas(str(OUT), pagesize=(WIDTH, HEIGHT), invariant=1)
    c.setTitle("Data science techniques: student field guide")
    c.setAuthor("Data science workshop")
    c.setSubject("Illustrated techniques for the synthetic AI product analytics workshop")
    cover(c)
    for number, page in enumerate(PAGES, start=1):
        topic_page(c, page, number)
    for i, page in enumerate(DICTIONARY, start=1):
        dictionary_page(c, page, len(PAGES) + i + 1)
    c.save()
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
