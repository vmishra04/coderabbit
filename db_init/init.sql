DROP TABLE IF EXISTS public.node_status;
CREATE TABLE
  public.node_status (
    observed_datetime TIMESTAMPTZ,
    node VARCHAR(40),
    online BOOLEAN
  );

COPY public.node_status FROM '/docker-entrypoint-initdb.d/node_status.csv' DELIMITER ',' CSV HEADER;

DROP TABLE IF EXISTS public.observed_price;
CREATE TABLE
  public.observed_price (
    observed_datetime TIMESTAMPTZ,
    node VARCHAR(40),
    price float
  );
COPY public.observed_price FROM '/docker-entrypoint-initdb.d/observed_price.csv' DELIMITER ',' CSV HEADER;

DROP TABLE IF EXISTS public.forecasted_price;
CREATE TABLE
  public.forecasted_price (
    analysis_datetime TIMESTAMPTZ,
    forecast_datetime TIMESTAMPTZ,
    node VARCHAR(40),
    price float
  );
COPY public.forecasted_price FROM '/docker-entrypoint-initdb.d/forecasted_price.csv' DELIMITER ',' CSV HEADER;
