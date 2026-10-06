-- One row per known customer with a positive purchase in the previous 90 days.
-- All predictors precede :cutoff. Outcome is [cutoff, cutoff + 30 days).
WITH history AS (
 SELECT customer, MAX(date) AS last_date, MIN(date) AS first_date,
        COUNT(*) AS frequency, SUM(amount) AS spend
 FROM invoices WHERE date >= :start AND date < :cutoff GROUP BY customer
), outcomes AS (
 SELECT DISTINCT customer FROM invoices WHERE date >= :cutoff AND date < :end
), latest AS (
 SELECT customer, country, ROW_NUMBER() OVER (PARTITION BY customer ORDER BY date DESC, invoice) AS rn
 FROM invoices WHERE date >= :start AND date < :cutoff
)
SELECT h.customer, l.country,
       julianday(:cutoff) - julianday(h.last_date) AS recency,
       h.frequency, h.spend,
       julianday(:cutoff) - julianday(h.first_date) AS observed_tenure,
       CASE WHEN o.customer IS NULL THEN 0 ELSE 1 END AS repeat
FROM history h JOIN latest l ON h.customer=l.customer AND l.rn=1
LEFT JOIN outcomes o ON h.customer=o.customer
ORDER BY h.customer;
