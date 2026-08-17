package za.co.tenderhub
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import org.junit.*
import za.co.tenderhub.domain.model.*
import za.co.tenderhub.ui.screens.*
class NotificationRenderingTest{@get:Rule val compose=createComposeRule();private val item=TenderNotification("n1","TENDER_CLOSING_SOON","Tender closes tomorrow","Security Services","t1",null,"NORMAL",null,"2026-08-17T10:00:00Z",null)
 @Test fun unreadNotificationRendersAndNavigates(){var opened=false;compose.setContent{NotificationCenterScreen(DataState.Success(listOf(item)),{},{opened=true},{})};compose.onNodeWithText("⚠ Tender closes tomorrow").assertIsDisplayed().performClick();Assert.assertTrue(opened)}
 @Test fun settingsExposeConsentControls(){val p=NotificationPreference("p",true,true,true,false,false,true,true,"22:00:00","07:00:00","Africa/Johannesburg","2026-08-17");compose.setContent{NotificationSettingsScreen(DataState.Success(p),false,{}, {})};compose.onNodeWithText("New tender matches").assertIsDisplayed();compose.onNodeWithText("Push client configuration is not installed in this build.").assertIsDisplayed()}}
