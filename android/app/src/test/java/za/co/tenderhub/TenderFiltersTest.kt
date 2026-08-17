package za.co.tenderhub
import org.junit.Assert.assertEquals
import org.junit.Test
import za.co.tenderhub.domain.model.TenderFilters
class TenderFiltersTest{@Test fun `active filters are counted and retained`(){val filters=TenderFilters(provinceId="kzn",category="Construction",closingFrom="2026-08-01",status="OPEN");assertEquals(4,filters.activeCount());assertEquals("kzn",filters.provinceId)}}
