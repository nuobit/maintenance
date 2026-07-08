16.0.1.1.2 (2026-07-09)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Fix ``total_purchase_amount`` computation for maintenance requests without a
  company. ``maintenance.request.company_id`` is optional, but the purchase
  amount was converted passing it straight to ``res.currency._convert``, which
  asserts that a company is set. It now falls back to the active company,
  mirroring what ``_compute_currency_id`` already does for the currency.
