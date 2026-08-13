"""Restore the Finance workspace chart and card configuration."""

from backdesk.patches.v0_0_2.repair_financial_charts import (
    repair_finance_customer_deposits_card,
    repair_profit_and_loss_dashboard_source,
    repair_worst_projects_chart,
)


def execute():
    repair_profit_and_loss_dashboard_source()
    repair_worst_projects_chart()
    repair_finance_customer_deposits_card()
