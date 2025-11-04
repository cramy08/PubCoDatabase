INSERT INTO public.baskets (slug, name, method) VALUES
('vertical_software','Vertical Software','equal_weight'),
('semi_cap','Semiconductor Capital Equipment','equal_weight')
ON CONFLICT (slug) DO NOTHING;

-- vertical_software
INSERT INTO public.basket_members (slug, ticker, valid_from) VALUES
('vertical_software','TYL',CURRENT_DATE),
('vertical_software','VEEV',CURRENT_DATE),
('vertical_software','PAYC',CURRENT_DATE),
('vertical_software','WDAY',CURRENT_DATE),
('vertical_software','MNDY',CURRENT_DATE),
('vertical_software','SMAR',CURRENT_DATE),
('vertical_software','NOW',CURRENT_DATE),
('vertical_software','ALKT',CURRENT_DATE),
('vertical_software','PTC',CURRENT_DATE),
('vertical_software','ANSS',CURRENT_DATE)
ON CONFLICT DO NOTHING;

-- semi_cap
INSERT INTO public.basket_members (slug, ticker, valid_from) VALUES
('semi_cap','ASML',CURRENT_DATE),
('semi_cap','AMAT',CURRENT_DATE),
('semi_cap','LRCX',CURRENT_DATE),
('semi_cap','KLAC',CURRENT_DATE),
('semi_cap','TER',CURRENT_DATE),
('semi_cap','ONTO',CURRENT_DATE),
('semi_cap','ACLS',CURRENT_DATE),
('semi_cap','AEHR',CURRENT_DATE),
('semi_cap','COHR',CURRENT_DATE),
('semi_cap','NVMI',CURRENT_DATE)
ON CONFLICT DO NOTHING;
