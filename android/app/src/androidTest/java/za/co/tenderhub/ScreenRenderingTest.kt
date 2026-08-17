package za.co.tenderhub
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import org.junit.Rule
import org.junit.Test
import za.co.tenderhub.ui.screens.WelcomeScreen
class ScreenRenderingTest{@get:Rule val compose=createComposeRule();@Test fun welcomeRenders(){compose.setContent{WelcomeScreen({},{})};compose.onNodeWithText("TenderHub SA").assertIsDisplayed();compose.onNodeWithText("Log in").assertIsDisplayed()}}
