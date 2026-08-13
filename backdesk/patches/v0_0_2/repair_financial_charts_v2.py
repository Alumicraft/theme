"""Reapply corrected financial chart configuration on already-migrated sites."""

from backdesk.patches.v0_0_2.repair_financial_charts import (
    repair_profit_and_loss_charts,
    repair_worst_projects_chart,
    repair_worst_projects_report,
)


def execute():
    repair_profit_and_loss_charts()
    repair_worst_projects_report()
    repair_worst_projects_chart()
