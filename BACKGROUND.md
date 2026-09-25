# Background

Domain context for the Parcel Locker Network analysis. This exists so the analysis is
grounded in how parcel-locker networks actually grow, rather than being an abstract
exercise in network optimisation.

---

## 1. Parcel lockers and out-of-home delivery

A parcel locker is a bank of self-service compartments where a courier drops parcels and
recipients collect them with a code, usually at any hour. For a delivery operator, lockers
turn many individual doorstep stops into one stop per site. That makes them much cheaper
per parcel than home delivery, and it is why lockers are often the first service an
operator launches in a new area.

Lockers are almost always hosted by someone else. The operator signs an agreement with a
retailer or property owner, who provides space, power and footfall in exchange for
visitors coming to the store. Grocery stores, kiosks and shopping centres are the natural
hosts: they are spread through residential areas, open long hours and visited often.

Two planning questions follow for any operator entering a city:

- **How many sites?** Each locker has an installation and running cost. More sites mean
  shorter walks for customers, but each extra site adds less than the one before.
- **Where?** Sites should go where they bring the most people within a short walk, but
  they can only go where a host agreement is plausible.

This project answers both for one city.

---

## 2. Budbee, and why these location types

Budbee is the consumer-facing brand of Instabee, a last-mile e-commerce delivery company
formed in 2022 from Budbee and Instabox. Budbee has operated in Finland since 2018, with
evening home delivery in selected postcode areas of about 19 municipalities (Helsinki
region, Tampere, Turku, Lahti, Jyvaskyla, Kuopio, Joensuu, Oulu and neighbouring towns)
and a network of parcel lockers called Budbee Box.

Budbee has been growing lockers-first. Recent announced expansions have been locker-only:
Pori and Rauma (2024, Pori with home delivery too), Mikkeli and Savonlinna (early 2025),
15 smaller towns in May 2025, Simo, Kemi, Keminmaa, Tornio and Ii (late 2025), and
Kokkola, Pietarsaari, Uusikaarlepyy, Voyri and Oravainen (March 2026). Sizing and placing
a locker network is therefore the practical question behind this expansion pattern.

Budbee's press releases name the chains that host its lockers: S Group (including
HOK-Elanto), K Group, Lidl and R-kioski stores. Budbee Boxes are also found in shopping
centres (for example Sello and A Bloc in Espoo). This project therefore restricts candidate
sites to exactly these location types. It does not use any Budbee data: Budbee's locker
locations are not publicly available, and the analysis is a from-scratch design, not a
description of Budbee's real network.

Other operators in Finland (Posti, Matkahuolto and others) use broadly similar host
types, so the method is general.

---

## 3. Why Espoo

Espoo (about 320,000 residents) plus Kauniainen (about 10,000, enclosed by Espoo) is a
polycentric city: separate centres at Tapiola, Leppavaara, Matinkyla, Espoon keskus,
Espoonlahti and Kauklahti, strung along the metro, the coastal corridor and the rail line,
with lower-density suburbs between them and sparse rural land in the north. That structure
means walking access varies a lot from place to place, which makes the site-selection
problem, and the maps, informative. A dense single-core city would give a less interesting
answer.

Espoo is also inside the area covered by HSY's open 250 m population grid, which is fine
enough for walking-distance analysis. Outside the capital region only a 1 km open grid
exists, which is too coarse (one cell is about a 12-minute walk across).

---

## 4. Technical concepts used

Short definitions, at the level of detail the project requires.

**Population grid.** HSY (Helsinki Region Environmental Services) publishes resident
counts for 250 m squares across the capital region. Each populated square is treated as
one point of demand at its centre, weighted by its residents. A 250 m cell is itself about
a 3-minute walk across, so walking-time bands finer than about 3 minutes are not
meaningful.

**Network walking distance.** Distance measured along the actual street and path network
(from OpenStreetMap), not in a straight line. In Espoo, water, motorways, railways and
large green areas mean two points close as the crow flies can be a long walk apart.

**Snapping.** Cell centres and store locations rarely sit exactly on a path, so each is
attached to its nearest network node. The gap (the snap distance) is added to the walk.
Cells very far from any path (mostly water or forest) are flagged.

**Shortest paths (Dijkstra).** A standard algorithm that finds the shortest network
distance from one point to every other point. Run once per candidate site, it gives the
walking time from that site to every populated cell.

**Greedy site selection.** Start with no lockers. Add the single candidate site that
reduces total resident walking time the most. Recompute everyone's nearest locker, then
repeat. This is a standard, easy-to-explain heuristic for the classic "p-median" location
problem. It does not guarantee the mathematically best set for a given number of sites,
but it is close in practice and, unlike an exact solver, it produces a natural build
order: site 1 is where an operator would start.

**Walk cap.** In the objective, walks longer than 30 minutes count as 30. Without this, a
few remote rural cells could pull sites away from where most people live.

**Coverage curve.** The share of residents within a 10-minute walk (and the average walk)
plotted against the number of lockers. It rises steeply at first and then flattens:
early sites in dense centres serve many people each, later sites in the suburbs serve few.
The shape of that curve is the cost-versus-coverage trade-off an operator has to decide on.

**Walking speed.** 4.8 km/h, or 80 metres per minute, a common planning assumption.

---

## 5. Known limitations

Worth stating openly in any write-up.

- This is a from-scratch design on open data, not an audit of any operator's actual
  network. Real networks already exist and grew under constraints this model ignores
  (which hosts agreed, when, and at what cost).
- Residents stand in for demand. Many people collect parcels near work, on a commute or
  at a store they already visit, which a home-based measure misses.
- Candidate sites are limited to the location types Budbee currently uses and come from
  OpenStreetMap, which may miss some stores (R-kioski in particular).
- One locker per site, with no capacity limit.
- Lockers are placed only inside Espoo and Kauniainen. Residents near the Helsinki
  boundary could in reality use lockers across it, so edge areas look slightly worse
  served than they are.
- The 250 m grid limits resolution, and HSY suppresses detail for small cells for privacy.
- Walking only. Some residents would drive to a locker.
