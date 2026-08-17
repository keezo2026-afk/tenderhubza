package za.co.tenderhub
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import org.junit.Rule
import org.junit.Test
import za.co.tenderhub.domain.model.Tender
import za.co.tenderhub.ui.screens.*
class SavedDiscoveryRenderingTest{@get:Rule val compose=createComposeRule();private val tender=Tender("1","ocds-1","ABC-123","Construction tender","Public Works","KwaZulu-Natal","eThekwini","Construction","open","2026-08-01","2026-09-01","11:00",null,"ZAR","OPEN","2026-08-01","2026-08-01")
 @Test fun savedButtonReflectsServerState(){compose.setContent{TenderCardView(tender,true,{}){}};compose.onNodeWithText("Saved").assertIsDisplayed()}
 @Test fun savedSearchShowsAlertStatus(){val search=SavedSearch("s1","KZN Construction","construction",emptyMap(),"relevance",true,"2026","2026");compose.setContent{SavedSearchesScreen(DataState.Success(listOf(search)),{},{},{_,_->},{},{})};compose.onNodeWithText("🔔 Alerts ON").assertIsDisplayed()}
 @Test fun emptySavedStateOffersSearch(){compose.setContent{SavedTendersScreen(DataState.Empty,emptySet(),{},{},{},{},{})};compose.onNodeWithText("You haven't saved any tenders yet.").assertIsDisplayed();compose.onNodeWithText("Search tenders").assertIsDisplayed()}}
