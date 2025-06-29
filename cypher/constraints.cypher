CREATE INDEX FOR (u:UUID) ON (u.id);
CREATE INDEX FOR (c:Color) ON (c.value);
CREATE INDEX FOR (t:Temperature) ON (t.value);
CREATE INDEX FOR (h:Humidity) ON (h.value);
CREATE INDEX FOR (ts:Timestamp) ON (ts.value);
CREATE INDEX FOR (ec:EnergyCost) ON (ec.value);
CREATE INDEX FOR (e:EnergyConsume) ON (e.value);
