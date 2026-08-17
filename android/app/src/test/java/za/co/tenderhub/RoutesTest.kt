package za.co.tenderhub
import org.junit.Assert.assertEquals
import org.junit.Test
import za.co.tenderhub.ui.navigation.Routes
class RoutesTest{@Test fun `all phase zero routes are unique`(){val routes=listOf(Routes.Splash,Routes.Welcome,Routes.Login,Routes.SignUp,Routes.Forgot,Routes.Home,Routes.Search,Routes.Saved,Routes.Notifications,Routes.Profile,Routes.Account,Routes.SavedSearches);assertEquals(routes.size,routes.distinct().size)}}
