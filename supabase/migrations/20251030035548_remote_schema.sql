drop extension if exists "pg_net";

create sequence "public"."prices_daily_log_id_seq";


  create table "public"."basket_members" (
    "slug" text not null,
    "ticker" text not null,
    "weight" numeric,
    "valid_from" date not null,
    "valid_to" date
      );



  create table "public"."baskets" (
    "slug" text not null,
    "name" text not null,
    "method" text not null,
    "base_dt" date,
    "base_value" numeric,
    "created_at" timestamp with time zone not null default now()
      );



  create table "public"."factor_series" (
    "slug" text not null,
    "name" text not null,
    "category" text,
    "method" text,
    "meta" jsonb default '{}'::jsonb,
    "created_at" timestamp with time zone not null default now()
      );



  create table "public"."factor_signals" (
    "run_id" uuid not null,
    "dt" date not null,
    "ticker" text not null,
    "factor_slug" text not null,
    "z_score" numeric,
    "entry_signal" boolean,
    "exit_signal" boolean,
    "hedge_weights" jsonb,
    "meta" jsonb default '{}'::jsonb,
    "created_at" timestamp with time zone default now()
      );



  create table "public"."factor_values" (
    "slug" text not null,
    "dt" date not null,
    "level" numeric,
    "r_1d" numeric,
    "r_20d" numeric,
    "r_60d" numeric,
    "r_252d" numeric,
    "mean_r1d_252" numeric,
    "std_r1d_252" numeric,
    "z_r1d_252" numeric,
    "mean_lvl_252" numeric,
    "std_lvl_252" numeric,
    "z_lvl_252" numeric,
    "source" text default 'excel'::text
      );



  create table "public"."factors" (
    "factor_id" uuid not null default gen_random_uuid(),
    "name" text not null,
    "description" text,
    "source" text default 'custom'::text,
    "category" text
      );



  create table "public"."instrument_covariances" (
    "dt" date not null,
    "ticker_1" text not null,
    "ticker_2" text not null,
    "covariance" numeric not null,
    "lookback_days" integer not null,
    "method" text default 'sample'::text
      );



  create table "public"."instrument_factor_exposures" (
    "ticker" text not null,
    "factor_id" uuid not null,
    "dt" date not null,
    "exposure" numeric not null
      );



  create table "public"."instrument_tags" (
    "ticker" text not null,
    "tag" text not null,
    "valid_from" date not null,
    "valid_to" date
      );



  create table "public"."instruments" (
    "ticker" text not null,
    "name" text,
    "asset_class" text,
    "exchange" text,
    "vendor_symbol" text,
    "is_delisted" boolean default false,
    "meta" jsonb default '{}'::jsonb
      );



  create table "public"."portfolio_positions" (
    "portfolio_id" uuid not null,
    "ticker" text not null,
    "weight" numeric not null,
    "valid_from" date not null,
    "valid_to" date
      );



  create table "public"."portfolios" (
    "portfolio_id" uuid not null default gen_random_uuid(),
    "name" text not null
      );



  create table "public"."prices_daily" (
    "ticker" text not null,
    "dt" date not null,
    "open" numeric(18,6),
    "high" numeric(18,6),
    "low" numeric(18,6),
    "close" numeric(18,6),
    "adj_close" numeric(18,6),
    "volume" bigint,
    "source" text default 'yfinance'::text,
    "inserted_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now()
      );



  create table "public"."prices_daily_log" (
    "id" bigint not null default nextval('public.prices_daily_log_id_seq'::regclass),
    "run_id" uuid not null,
    "created_at" timestamp with time zone not null default now(),
    "ticker" text not null,
    "source" text not null,
    "fetch_start" date,
    "fetch_end" date,
    "rows_upserted" integer not null,
    "status" text not null,
    "error_message" text
      );



  create table "public"."signal_runs" (
    "run_id" uuid not null default gen_random_uuid(),
    "started_at" timestamp with time zone not null default now(),
    "completed_at" timestamp with time zone,
    "status" text not null,
    "factors_run" text[] not null,
    "notes" text
      );



  create table "public"."tags" (
    "tag" text not null,
    "tag_type" text not null
      );



  create table "public"."universe_membership" (
    "ticker" text not null,
    "universe" text not null,
    "valid_from" date not null,
    "valid_to" date
      );


alter sequence "public"."prices_daily_log_id_seq" owned by "public"."prices_daily_log"."id";

CREATE UNIQUE INDEX basket_members_pkey ON public.basket_members USING btree (slug, ticker, valid_from);

CREATE UNIQUE INDEX baskets_pkey ON public.baskets USING btree (slug);

CREATE INDEX exposures_idx ON public.instrument_factor_exposures USING btree (ticker, factor_id, dt);

CREATE UNIQUE INDEX factor_series_pkey ON public.factor_series USING btree (slug);

CREATE UNIQUE INDEX factor_signals_pkey ON public.factor_signals USING btree (dt, ticker, factor_slug);

CREATE UNIQUE INDEX factor_values_pkey ON public.factor_values USING btree (slug, dt);

CREATE INDEX factor_values_slug_dt_idx ON public.factor_values USING btree (slug, dt);

CREATE UNIQUE INDEX factors_name_key ON public.factors USING btree (name);

CREATE UNIQUE INDEX factors_pkey ON public.factors USING btree (factor_id);

CREATE UNIQUE INDEX instrument_covariances_pkey ON public.instrument_covariances USING btree (dt, ticker_1, ticker_2);

CREATE UNIQUE INDEX instrument_factor_exposures_pkey ON public.instrument_factor_exposures USING btree (ticker, factor_id, dt);

CREATE UNIQUE INDEX instrument_tags_pkey ON public.instrument_tags USING btree (ticker, tag, valid_from);

CREATE UNIQUE INDEX instruments_pkey ON public.instruments USING btree (ticker);

CREATE UNIQUE INDEX portfolio_positions_pkey ON public.portfolio_positions USING btree (portfolio_id, ticker, valid_from);

CREATE UNIQUE INDEX portfolios_name_key ON public.portfolios USING btree (name);

CREATE UNIQUE INDEX portfolios_pkey ON public.portfolios USING btree (portfolio_id);

CREATE INDEX positions_idx ON public.portfolio_positions USING btree (portfolio_id, ticker, valid_from, valid_to);

CREATE INDEX prices_daily_dt_idx ON public.prices_daily USING btree (dt);

CREATE UNIQUE INDEX prices_daily_log_pkey ON public.prices_daily_log USING btree (id);

CREATE INDEX prices_daily_log_run_id_idx ON public.prices_daily_log USING btree (run_id);

CREATE INDEX prices_daily_log_ticker_idx ON public.prices_daily_log USING btree (ticker);

CREATE UNIQUE INDEX prices_daily_pk ON public.prices_daily USING btree (ticker, dt);

CREATE INDEX prices_daily_ticker_dt_idx ON public.prices_daily USING btree (ticker, dt);

CREATE UNIQUE INDEX prices_daily_ticker_dt_unique ON public.prices_daily USING btree (ticker, dt);

CREATE UNIQUE INDEX signal_runs_pkey ON public.signal_runs USING btree (run_id);

CREATE INDEX tags_idx ON public.instrument_tags USING btree (tag, ticker, valid_from, valid_to);

CREATE UNIQUE INDEX tags_pkey ON public.tags USING btree (tag);

CREATE INDEX universe_membership_idx ON public.universe_membership USING btree (universe, ticker, valid_from, valid_to);

CREATE UNIQUE INDEX universe_membership_pkey ON public.universe_membership USING btree (ticker, universe, valid_from);

alter table "public"."basket_members" add constraint "basket_members_pkey" PRIMARY KEY using index "basket_members_pkey";

alter table "public"."baskets" add constraint "baskets_pkey" PRIMARY KEY using index "baskets_pkey";

alter table "public"."factor_series" add constraint "factor_series_pkey" PRIMARY KEY using index "factor_series_pkey";

alter table "public"."factor_signals" add constraint "factor_signals_pkey" PRIMARY KEY using index "factor_signals_pkey";

alter table "public"."factor_values" add constraint "factor_values_pkey" PRIMARY KEY using index "factor_values_pkey";

alter table "public"."factors" add constraint "factors_pkey" PRIMARY KEY using index "factors_pkey";

alter table "public"."instrument_covariances" add constraint "instrument_covariances_pkey" PRIMARY KEY using index "instrument_covariances_pkey";

alter table "public"."instrument_factor_exposures" add constraint "instrument_factor_exposures_pkey" PRIMARY KEY using index "instrument_factor_exposures_pkey";

alter table "public"."instrument_tags" add constraint "instrument_tags_pkey" PRIMARY KEY using index "instrument_tags_pkey";

alter table "public"."instruments" add constraint "instruments_pkey" PRIMARY KEY using index "instruments_pkey";

alter table "public"."portfolio_positions" add constraint "portfolio_positions_pkey" PRIMARY KEY using index "portfolio_positions_pkey";

alter table "public"."portfolios" add constraint "portfolios_pkey" PRIMARY KEY using index "portfolios_pkey";

alter table "public"."prices_daily" add constraint "prices_daily_pk" PRIMARY KEY using index "prices_daily_pk";

alter table "public"."prices_daily_log" add constraint "prices_daily_log_pkey" PRIMARY KEY using index "prices_daily_log_pkey";

alter table "public"."signal_runs" add constraint "signal_runs_pkey" PRIMARY KEY using index "signal_runs_pkey";

alter table "public"."tags" add constraint "tags_pkey" PRIMARY KEY using index "tags_pkey";

alter table "public"."universe_membership" add constraint "universe_membership_pkey" PRIMARY KEY using index "universe_membership_pkey";

alter table "public"."basket_members" add constraint "basket_members_slug_fkey" FOREIGN KEY (slug) REFERENCES public.baskets(slug) ON DELETE CASCADE not valid;

alter table "public"."basket_members" validate constraint "basket_members_slug_fkey";

alter table "public"."baskets" add constraint "baskets_method_check" CHECK ((method = ANY (ARRAY['equal_weight'::text, 'cap_weight'::text]))) not valid;

alter table "public"."baskets" validate constraint "baskets_method_check";

alter table "public"."factor_signals" add constraint "factor_signals_factor_slug_fkey" FOREIGN KEY (factor_slug) REFERENCES public.factor_series(slug) not valid;

alter table "public"."factor_signals" validate constraint "factor_signals_factor_slug_fkey";

alter table "public"."factor_signals" add constraint "factor_signals_run_id_fkey" FOREIGN KEY (run_id) REFERENCES public.signal_runs(run_id) not valid;

alter table "public"."factor_signals" validate constraint "factor_signals_run_id_fkey";

alter table "public"."factor_signals" add constraint "factor_signals_ticker_fkey" FOREIGN KEY (ticker) REFERENCES public.instruments(ticker) not valid;

alter table "public"."factor_signals" validate constraint "factor_signals_ticker_fkey";

alter table "public"."factor_values" add constraint "factor_values_slug_fkey" FOREIGN KEY (slug) REFERENCES public.factor_series(slug) ON DELETE CASCADE not valid;

alter table "public"."factor_values" validate constraint "factor_values_slug_fkey";

alter table "public"."factors" add constraint "factors_name_key" UNIQUE using index "factors_name_key";

alter table "public"."instrument_covariances" add constraint "instrument_covariances_ticker_1_fkey" FOREIGN KEY (ticker_1) REFERENCES public.instruments(ticker) not valid;

alter table "public"."instrument_covariances" validate constraint "instrument_covariances_ticker_1_fkey";

alter table "public"."instrument_covariances" add constraint "instrument_covariances_ticker_2_fkey" FOREIGN KEY (ticker_2) REFERENCES public.instruments(ticker) not valid;

alter table "public"."instrument_covariances" validate constraint "instrument_covariances_ticker_2_fkey";

alter table "public"."instrument_factor_exposures" add constraint "instrument_factor_exposures_factor_id_fkey" FOREIGN KEY (factor_id) REFERENCES public.factors(factor_id) ON DELETE CASCADE not valid;

alter table "public"."instrument_factor_exposures" validate constraint "instrument_factor_exposures_factor_id_fkey";

alter table "public"."instrument_factor_exposures" add constraint "instrument_factor_exposures_ticker_fkey" FOREIGN KEY (ticker) REFERENCES public.instruments(ticker) ON DELETE CASCADE not valid;

alter table "public"."instrument_factor_exposures" validate constraint "instrument_factor_exposures_ticker_fkey";

alter table "public"."instrument_tags" add constraint "instrument_tags_tag_fkey" FOREIGN KEY (tag) REFERENCES public.tags(tag) ON DELETE CASCADE not valid;

alter table "public"."instrument_tags" validate constraint "instrument_tags_tag_fkey";

alter table "public"."instrument_tags" add constraint "instrument_tags_ticker_fkey" FOREIGN KEY (ticker) REFERENCES public.instruments(ticker) ON DELETE CASCADE not valid;

alter table "public"."instrument_tags" validate constraint "instrument_tags_ticker_fkey";

alter table "public"."instruments" add constraint "instruments_asset_class_check" CHECK ((asset_class = ANY (ARRAY['Equity'::text, 'ETF'::text, 'MF'::text, 'ADR'::text, 'Bond'::text, 'Other'::text]))) not valid;

alter table "public"."instruments" validate constraint "instruments_asset_class_check";

alter table "public"."portfolio_positions" add constraint "portfolio_positions_portfolio_id_fkey" FOREIGN KEY (portfolio_id) REFERENCES public.portfolios(portfolio_id) ON DELETE CASCADE not valid;

alter table "public"."portfolio_positions" validate constraint "portfolio_positions_portfolio_id_fkey";

alter table "public"."portfolio_positions" add constraint "portfolio_positions_ticker_fkey" FOREIGN KEY (ticker) REFERENCES public.instruments(ticker) not valid;

alter table "public"."portfolio_positions" validate constraint "portfolio_positions_ticker_fkey";

alter table "public"."portfolios" add constraint "portfolios_name_key" UNIQUE using index "portfolios_name_key";

alter table "public"."prices_daily" add constraint "prices_daily_ticker_dt_unique" UNIQUE using index "prices_daily_ticker_dt_unique";

alter table "public"."prices_daily_log" add constraint "prices_daily_log_status_check" CHECK ((status = ANY (ARRAY['ok'::text, 'skip'::text, 'err'::text]))) not valid;

alter table "public"."prices_daily_log" validate constraint "prices_daily_log_status_check";

alter table "public"."signal_runs" add constraint "signal_runs_status_check" CHECK ((status = ANY (ARRAY['ok'::text, 'failed'::text, 'partial'::text]))) not valid;

alter table "public"."signal_runs" validate constraint "signal_runs_status_check";

alter table "public"."universe_membership" add constraint "universe_membership_ticker_fkey" FOREIGN KEY (ticker) REFERENCES public.instruments(ticker) ON DELETE CASCADE not valid;

alter table "public"."universe_membership" validate constraint "universe_membership_ticker_fkey";

set check_function_bodies = off;

CREATE OR REPLACE FUNCTION public.touch_prices_daily_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
begin
  new.updated_at := now();
  return new;
end $function$
;

create or replace view "public"."v_instrument_tags_today" as  SELECT it.ticker,
    it.tag,
    t.tag_type
   FROM (public.instrument_tags it
     JOIN public.tags t USING (tag))
  WHERE ((it.valid_from <= CURRENT_DATE) AND ((it.valid_to IS NULL) OR (it.valid_to >= CURRENT_DATE)));


create or replace view "public"."v_portfolio_positions_today" as  SELECT p.name AS portfolio,
    pp.ticker,
    pp.weight
   FROM (public.portfolio_positions pp
     JOIN public.portfolios p USING (portfolio_id))
  WHERE ((pp.valid_from <= CURRENT_DATE) AND ((pp.valid_to IS NULL) OR (pp.valid_to >= CURRENT_DATE)));


create or replace view "public"."v_universe_active_today" as  SELECT ticker,
    universe
   FROM public.universe_membership
  WHERE ((valid_from <= CURRENT_DATE) AND ((valid_to IS NULL) OR (valid_to >= CURRENT_DATE)));


grant delete on table "public"."basket_members" to "anon";

grant insert on table "public"."basket_members" to "anon";

grant references on table "public"."basket_members" to "anon";

grant select on table "public"."basket_members" to "anon";

grant trigger on table "public"."basket_members" to "anon";

grant truncate on table "public"."basket_members" to "anon";

grant update on table "public"."basket_members" to "anon";

grant delete on table "public"."basket_members" to "authenticated";

grant insert on table "public"."basket_members" to "authenticated";

grant references on table "public"."basket_members" to "authenticated";

grant select on table "public"."basket_members" to "authenticated";

grant trigger on table "public"."basket_members" to "authenticated";

grant truncate on table "public"."basket_members" to "authenticated";

grant update on table "public"."basket_members" to "authenticated";

grant delete on table "public"."basket_members" to "service_role";

grant insert on table "public"."basket_members" to "service_role";

grant references on table "public"."basket_members" to "service_role";

grant select on table "public"."basket_members" to "service_role";

grant trigger on table "public"."basket_members" to "service_role";

grant truncate on table "public"."basket_members" to "service_role";

grant update on table "public"."basket_members" to "service_role";

grant delete on table "public"."baskets" to "anon";

grant insert on table "public"."baskets" to "anon";

grant references on table "public"."baskets" to "anon";

grant select on table "public"."baskets" to "anon";

grant trigger on table "public"."baskets" to "anon";

grant truncate on table "public"."baskets" to "anon";

grant update on table "public"."baskets" to "anon";

grant delete on table "public"."baskets" to "authenticated";

grant insert on table "public"."baskets" to "authenticated";

grant references on table "public"."baskets" to "authenticated";

grant select on table "public"."baskets" to "authenticated";

grant trigger on table "public"."baskets" to "authenticated";

grant truncate on table "public"."baskets" to "authenticated";

grant update on table "public"."baskets" to "authenticated";

grant delete on table "public"."baskets" to "service_role";

grant insert on table "public"."baskets" to "service_role";

grant references on table "public"."baskets" to "service_role";

grant select on table "public"."baskets" to "service_role";

grant trigger on table "public"."baskets" to "service_role";

grant truncate on table "public"."baskets" to "service_role";

grant update on table "public"."baskets" to "service_role";

grant delete on table "public"."factor_series" to "anon";

grant insert on table "public"."factor_series" to "anon";

grant references on table "public"."factor_series" to "anon";

grant select on table "public"."factor_series" to "anon";

grant trigger on table "public"."factor_series" to "anon";

grant truncate on table "public"."factor_series" to "anon";

grant update on table "public"."factor_series" to "anon";

grant delete on table "public"."factor_series" to "authenticated";

grant insert on table "public"."factor_series" to "authenticated";

grant references on table "public"."factor_series" to "authenticated";

grant select on table "public"."factor_series" to "authenticated";

grant trigger on table "public"."factor_series" to "authenticated";

grant truncate on table "public"."factor_series" to "authenticated";

grant update on table "public"."factor_series" to "authenticated";

grant delete on table "public"."factor_series" to "service_role";

grant insert on table "public"."factor_series" to "service_role";

grant references on table "public"."factor_series" to "service_role";

grant select on table "public"."factor_series" to "service_role";

grant trigger on table "public"."factor_series" to "service_role";

grant truncate on table "public"."factor_series" to "service_role";

grant update on table "public"."factor_series" to "service_role";

grant delete on table "public"."factor_signals" to "anon";

grant insert on table "public"."factor_signals" to "anon";

grant references on table "public"."factor_signals" to "anon";

grant select on table "public"."factor_signals" to "anon";

grant trigger on table "public"."factor_signals" to "anon";

grant truncate on table "public"."factor_signals" to "anon";

grant update on table "public"."factor_signals" to "anon";

grant delete on table "public"."factor_signals" to "authenticated";

grant insert on table "public"."factor_signals" to "authenticated";

grant references on table "public"."factor_signals" to "authenticated";

grant select on table "public"."factor_signals" to "authenticated";

grant trigger on table "public"."factor_signals" to "authenticated";

grant truncate on table "public"."factor_signals" to "authenticated";

grant update on table "public"."factor_signals" to "authenticated";

grant delete on table "public"."factor_signals" to "service_role";

grant insert on table "public"."factor_signals" to "service_role";

grant references on table "public"."factor_signals" to "service_role";

grant select on table "public"."factor_signals" to "service_role";

grant trigger on table "public"."factor_signals" to "service_role";

grant truncate on table "public"."factor_signals" to "service_role";

grant update on table "public"."factor_signals" to "service_role";

grant delete on table "public"."factor_values" to "anon";

grant insert on table "public"."factor_values" to "anon";

grant references on table "public"."factor_values" to "anon";

grant select on table "public"."factor_values" to "anon";

grant trigger on table "public"."factor_values" to "anon";

grant truncate on table "public"."factor_values" to "anon";

grant update on table "public"."factor_values" to "anon";

grant delete on table "public"."factor_values" to "authenticated";

grant insert on table "public"."factor_values" to "authenticated";

grant references on table "public"."factor_values" to "authenticated";

grant select on table "public"."factor_values" to "authenticated";

grant trigger on table "public"."factor_values" to "authenticated";

grant truncate on table "public"."factor_values" to "authenticated";

grant update on table "public"."factor_values" to "authenticated";

grant delete on table "public"."factor_values" to "service_role";

grant insert on table "public"."factor_values" to "service_role";

grant references on table "public"."factor_values" to "service_role";

grant select on table "public"."factor_values" to "service_role";

grant trigger on table "public"."factor_values" to "service_role";

grant truncate on table "public"."factor_values" to "service_role";

grant update on table "public"."factor_values" to "service_role";

grant delete on table "public"."factors" to "anon";

grant insert on table "public"."factors" to "anon";

grant references on table "public"."factors" to "anon";

grant select on table "public"."factors" to "anon";

grant trigger on table "public"."factors" to "anon";

grant truncate on table "public"."factors" to "anon";

grant update on table "public"."factors" to "anon";

grant delete on table "public"."factors" to "authenticated";

grant insert on table "public"."factors" to "authenticated";

grant references on table "public"."factors" to "authenticated";

grant select on table "public"."factors" to "authenticated";

grant trigger on table "public"."factors" to "authenticated";

grant truncate on table "public"."factors" to "authenticated";

grant update on table "public"."factors" to "authenticated";

grant delete on table "public"."factors" to "service_role";

grant insert on table "public"."factors" to "service_role";

grant references on table "public"."factors" to "service_role";

grant select on table "public"."factors" to "service_role";

grant trigger on table "public"."factors" to "service_role";

grant truncate on table "public"."factors" to "service_role";

grant update on table "public"."factors" to "service_role";

grant delete on table "public"."instrument_covariances" to "anon";

grant insert on table "public"."instrument_covariances" to "anon";

grant references on table "public"."instrument_covariances" to "anon";

grant select on table "public"."instrument_covariances" to "anon";

grant trigger on table "public"."instrument_covariances" to "anon";

grant truncate on table "public"."instrument_covariances" to "anon";

grant update on table "public"."instrument_covariances" to "anon";

grant delete on table "public"."instrument_covariances" to "authenticated";

grant insert on table "public"."instrument_covariances" to "authenticated";

grant references on table "public"."instrument_covariances" to "authenticated";

grant select on table "public"."instrument_covariances" to "authenticated";

grant trigger on table "public"."instrument_covariances" to "authenticated";

grant truncate on table "public"."instrument_covariances" to "authenticated";

grant update on table "public"."instrument_covariances" to "authenticated";

grant delete on table "public"."instrument_covariances" to "service_role";

grant insert on table "public"."instrument_covariances" to "service_role";

grant references on table "public"."instrument_covariances" to "service_role";

grant select on table "public"."instrument_covariances" to "service_role";

grant trigger on table "public"."instrument_covariances" to "service_role";

grant truncate on table "public"."instrument_covariances" to "service_role";

grant update on table "public"."instrument_covariances" to "service_role";

grant delete on table "public"."instrument_factor_exposures" to "anon";

grant insert on table "public"."instrument_factor_exposures" to "anon";

grant references on table "public"."instrument_factor_exposures" to "anon";

grant select on table "public"."instrument_factor_exposures" to "anon";

grant trigger on table "public"."instrument_factor_exposures" to "anon";

grant truncate on table "public"."instrument_factor_exposures" to "anon";

grant update on table "public"."instrument_factor_exposures" to "anon";

grant delete on table "public"."instrument_factor_exposures" to "authenticated";

grant insert on table "public"."instrument_factor_exposures" to "authenticated";

grant references on table "public"."instrument_factor_exposures" to "authenticated";

grant select on table "public"."instrument_factor_exposures" to "authenticated";

grant trigger on table "public"."instrument_factor_exposures" to "authenticated";

grant truncate on table "public"."instrument_factor_exposures" to "authenticated";

grant update on table "public"."instrument_factor_exposures" to "authenticated";

grant delete on table "public"."instrument_factor_exposures" to "service_role";

grant insert on table "public"."instrument_factor_exposures" to "service_role";

grant references on table "public"."instrument_factor_exposures" to "service_role";

grant select on table "public"."instrument_factor_exposures" to "service_role";

grant trigger on table "public"."instrument_factor_exposures" to "service_role";

grant truncate on table "public"."instrument_factor_exposures" to "service_role";

grant update on table "public"."instrument_factor_exposures" to "service_role";

grant delete on table "public"."instrument_tags" to "anon";

grant insert on table "public"."instrument_tags" to "anon";

grant references on table "public"."instrument_tags" to "anon";

grant select on table "public"."instrument_tags" to "anon";

grant trigger on table "public"."instrument_tags" to "anon";

grant truncate on table "public"."instrument_tags" to "anon";

grant update on table "public"."instrument_tags" to "anon";

grant delete on table "public"."instrument_tags" to "authenticated";

grant insert on table "public"."instrument_tags" to "authenticated";

grant references on table "public"."instrument_tags" to "authenticated";

grant select on table "public"."instrument_tags" to "authenticated";

grant trigger on table "public"."instrument_tags" to "authenticated";

grant truncate on table "public"."instrument_tags" to "authenticated";

grant update on table "public"."instrument_tags" to "authenticated";

grant delete on table "public"."instrument_tags" to "service_role";

grant insert on table "public"."instrument_tags" to "service_role";

grant references on table "public"."instrument_tags" to "service_role";

grant select on table "public"."instrument_tags" to "service_role";

grant trigger on table "public"."instrument_tags" to "service_role";

grant truncate on table "public"."instrument_tags" to "service_role";

grant update on table "public"."instrument_tags" to "service_role";

grant delete on table "public"."instruments" to "anon";

grant insert on table "public"."instruments" to "anon";

grant references on table "public"."instruments" to "anon";

grant select on table "public"."instruments" to "anon";

grant trigger on table "public"."instruments" to "anon";

grant truncate on table "public"."instruments" to "anon";

grant update on table "public"."instruments" to "anon";

grant delete on table "public"."instruments" to "authenticated";

grant insert on table "public"."instruments" to "authenticated";

grant references on table "public"."instruments" to "authenticated";

grant select on table "public"."instruments" to "authenticated";

grant trigger on table "public"."instruments" to "authenticated";

grant truncate on table "public"."instruments" to "authenticated";

grant update on table "public"."instruments" to "authenticated";

grant delete on table "public"."instruments" to "service_role";

grant insert on table "public"."instruments" to "service_role";

grant references on table "public"."instruments" to "service_role";

grant select on table "public"."instruments" to "service_role";

grant trigger on table "public"."instruments" to "service_role";

grant truncate on table "public"."instruments" to "service_role";

grant update on table "public"."instruments" to "service_role";

grant delete on table "public"."portfolio_positions" to "anon";

grant insert on table "public"."portfolio_positions" to "anon";

grant references on table "public"."portfolio_positions" to "anon";

grant select on table "public"."portfolio_positions" to "anon";

grant trigger on table "public"."portfolio_positions" to "anon";

grant truncate on table "public"."portfolio_positions" to "anon";

grant update on table "public"."portfolio_positions" to "anon";

grant delete on table "public"."portfolio_positions" to "authenticated";

grant insert on table "public"."portfolio_positions" to "authenticated";

grant references on table "public"."portfolio_positions" to "authenticated";

grant select on table "public"."portfolio_positions" to "authenticated";

grant trigger on table "public"."portfolio_positions" to "authenticated";

grant truncate on table "public"."portfolio_positions" to "authenticated";

grant update on table "public"."portfolio_positions" to "authenticated";

grant delete on table "public"."portfolio_positions" to "service_role";

grant insert on table "public"."portfolio_positions" to "service_role";

grant references on table "public"."portfolio_positions" to "service_role";

grant select on table "public"."portfolio_positions" to "service_role";

grant trigger on table "public"."portfolio_positions" to "service_role";

grant truncate on table "public"."portfolio_positions" to "service_role";

grant update on table "public"."portfolio_positions" to "service_role";

grant delete on table "public"."portfolios" to "anon";

grant insert on table "public"."portfolios" to "anon";

grant references on table "public"."portfolios" to "anon";

grant select on table "public"."portfolios" to "anon";

grant trigger on table "public"."portfolios" to "anon";

grant truncate on table "public"."portfolios" to "anon";

grant update on table "public"."portfolios" to "anon";

grant delete on table "public"."portfolios" to "authenticated";

grant insert on table "public"."portfolios" to "authenticated";

grant references on table "public"."portfolios" to "authenticated";

grant select on table "public"."portfolios" to "authenticated";

grant trigger on table "public"."portfolios" to "authenticated";

grant truncate on table "public"."portfolios" to "authenticated";

grant update on table "public"."portfolios" to "authenticated";

grant delete on table "public"."portfolios" to "service_role";

grant insert on table "public"."portfolios" to "service_role";

grant references on table "public"."portfolios" to "service_role";

grant select on table "public"."portfolios" to "service_role";

grant trigger on table "public"."portfolios" to "service_role";

grant truncate on table "public"."portfolios" to "service_role";

grant update on table "public"."portfolios" to "service_role";

grant delete on table "public"."prices_daily" to "anon";

grant insert on table "public"."prices_daily" to "anon";

grant references on table "public"."prices_daily" to "anon";

grant select on table "public"."prices_daily" to "anon";

grant trigger on table "public"."prices_daily" to "anon";

grant truncate on table "public"."prices_daily" to "anon";

grant update on table "public"."prices_daily" to "anon";

grant delete on table "public"."prices_daily" to "authenticated";

grant insert on table "public"."prices_daily" to "authenticated";

grant references on table "public"."prices_daily" to "authenticated";

grant select on table "public"."prices_daily" to "authenticated";

grant trigger on table "public"."prices_daily" to "authenticated";

grant truncate on table "public"."prices_daily" to "authenticated";

grant update on table "public"."prices_daily" to "authenticated";

grant delete on table "public"."prices_daily" to "service_role";

grant insert on table "public"."prices_daily" to "service_role";

grant references on table "public"."prices_daily" to "service_role";

grant select on table "public"."prices_daily" to "service_role";

grant trigger on table "public"."prices_daily" to "service_role";

grant truncate on table "public"."prices_daily" to "service_role";

grant update on table "public"."prices_daily" to "service_role";

grant delete on table "public"."prices_daily_log" to "anon";

grant insert on table "public"."prices_daily_log" to "anon";

grant references on table "public"."prices_daily_log" to "anon";

grant select on table "public"."prices_daily_log" to "anon";

grant trigger on table "public"."prices_daily_log" to "anon";

grant truncate on table "public"."prices_daily_log" to "anon";

grant update on table "public"."prices_daily_log" to "anon";

grant delete on table "public"."prices_daily_log" to "authenticated";

grant insert on table "public"."prices_daily_log" to "authenticated";

grant references on table "public"."prices_daily_log" to "authenticated";

grant select on table "public"."prices_daily_log" to "authenticated";

grant trigger on table "public"."prices_daily_log" to "authenticated";

grant truncate on table "public"."prices_daily_log" to "authenticated";

grant update on table "public"."prices_daily_log" to "authenticated";

grant delete on table "public"."prices_daily_log" to "service_role";

grant insert on table "public"."prices_daily_log" to "service_role";

grant references on table "public"."prices_daily_log" to "service_role";

grant select on table "public"."prices_daily_log" to "service_role";

grant trigger on table "public"."prices_daily_log" to "service_role";

grant truncate on table "public"."prices_daily_log" to "service_role";

grant update on table "public"."prices_daily_log" to "service_role";

grant delete on table "public"."signal_runs" to "anon";

grant insert on table "public"."signal_runs" to "anon";

grant references on table "public"."signal_runs" to "anon";

grant select on table "public"."signal_runs" to "anon";

grant trigger on table "public"."signal_runs" to "anon";

grant truncate on table "public"."signal_runs" to "anon";

grant update on table "public"."signal_runs" to "anon";

grant delete on table "public"."signal_runs" to "authenticated";

grant insert on table "public"."signal_runs" to "authenticated";

grant references on table "public"."signal_runs" to "authenticated";

grant select on table "public"."signal_runs" to "authenticated";

grant trigger on table "public"."signal_runs" to "authenticated";

grant truncate on table "public"."signal_runs" to "authenticated";

grant update on table "public"."signal_runs" to "authenticated";

grant delete on table "public"."signal_runs" to "service_role";

grant insert on table "public"."signal_runs" to "service_role";

grant references on table "public"."signal_runs" to "service_role";

grant select on table "public"."signal_runs" to "service_role";

grant trigger on table "public"."signal_runs" to "service_role";

grant truncate on table "public"."signal_runs" to "service_role";

grant update on table "public"."signal_runs" to "service_role";

grant delete on table "public"."tags" to "anon";

grant insert on table "public"."tags" to "anon";

grant references on table "public"."tags" to "anon";

grant select on table "public"."tags" to "anon";

grant trigger on table "public"."tags" to "anon";

grant truncate on table "public"."tags" to "anon";

grant update on table "public"."tags" to "anon";

grant delete on table "public"."tags" to "authenticated";

grant insert on table "public"."tags" to "authenticated";

grant references on table "public"."tags" to "authenticated";

grant select on table "public"."tags" to "authenticated";

grant trigger on table "public"."tags" to "authenticated";

grant truncate on table "public"."tags" to "authenticated";

grant update on table "public"."tags" to "authenticated";

grant delete on table "public"."tags" to "service_role";

grant insert on table "public"."tags" to "service_role";

grant references on table "public"."tags" to "service_role";

grant select on table "public"."tags" to "service_role";

grant trigger on table "public"."tags" to "service_role";

grant truncate on table "public"."tags" to "service_role";

grant update on table "public"."tags" to "service_role";

grant delete on table "public"."universe_membership" to "anon";

grant insert on table "public"."universe_membership" to "anon";

grant references on table "public"."universe_membership" to "anon";

grant select on table "public"."universe_membership" to "anon";

grant trigger on table "public"."universe_membership" to "anon";

grant truncate on table "public"."universe_membership" to "anon";

grant update on table "public"."universe_membership" to "anon";

grant delete on table "public"."universe_membership" to "authenticated";

grant insert on table "public"."universe_membership" to "authenticated";

grant references on table "public"."universe_membership" to "authenticated";

grant select on table "public"."universe_membership" to "authenticated";

grant trigger on table "public"."universe_membership" to "authenticated";

grant truncate on table "public"."universe_membership" to "authenticated";

grant update on table "public"."universe_membership" to "authenticated";

grant delete on table "public"."universe_membership" to "service_role";

grant insert on table "public"."universe_membership" to "service_role";

grant references on table "public"."universe_membership" to "service_role";

grant select on table "public"."universe_membership" to "service_role";

grant trigger on table "public"."universe_membership" to "service_role";

grant truncate on table "public"."universe_membership" to "service_role";

grant update on table "public"."universe_membership" to "service_role";

CREATE TRIGGER trg_touch_prices_daily BEFORE INSERT OR UPDATE ON public.prices_daily FOR EACH ROW EXECUTE FUNCTION public.touch_prices_daily_updated_at();


