package za.co.tenderhub
import androidx.test.core.app.ApplicationProvider
import org.junit.Assert.*
import org.junit.Test
import za.co.tenderhub.data.repository.SearchHistoryStore
class SearchHistoryTest{@Test fun historyIsLimitedRerunnableAndClearable(){val context=ApplicationProvider.getApplicationContext<android.content.Context>();context.getSharedPreferences("search_history",0).edit().clear().commit();val store=SearchHistoryStore(context);(1..12).forEach{store.add("query $it")};assertEquals(10,store.items.value.size);assertEquals("query 12",store.items.value.first());store.remove("query 12");assertFalse(store.items.value.contains("query 12"));store.clear();assertTrue(store.items.value.isEmpty())}}
