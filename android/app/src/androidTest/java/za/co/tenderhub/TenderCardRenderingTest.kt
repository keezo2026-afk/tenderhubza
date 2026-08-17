package za.co.tenderhub
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import org.junit.Rule
import org.junit.Test
import za.co.tenderhub.domain.model.Tender
import za.co.tenderhub.ui.screens.TenderCardView
class TenderCardRenderingTest{@get:Rule val compose=createComposeRule();@Test fun apiTenderRenders(){val tender=Tender("1","ocds-1","ZNT-1","Construction services","Public Works","KwaZulu-Natal",null,"Works","open","2026-08-01","2026-09-01","11:00",null,"ZAR","OPEN","2026-08-01","2026-08-01");compose.setContent{TenderCardView(tender){}};compose.onNodeWithText("Construction services").assertIsDisplayed();compose.onNodeWithText("Closes 1 Sep").assertIsDisplayed()}}
