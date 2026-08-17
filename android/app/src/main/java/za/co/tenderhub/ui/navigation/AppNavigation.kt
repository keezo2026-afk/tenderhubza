package za.co.tenderhub.ui.navigation
import androidx.compose.runtime.*
import androidx.navigation.compose.*
import za.co.tenderhub.ui.screens.*
@Composable fun AppNavigation(vm:AuthViewModel){val nav=rememberNavController();val state by vm.state.collectAsState();LaunchedEffect(state){when(state){is AuthState.Authenticated->nav.navigate(Routes.Home){popUpTo(0)};AuthState.Anonymous->if(nav.currentDestination?.route==Routes.Splash)nav.navigate(Routes.Welcome){popUpTo(Routes.Splash){inclusive=true}};else->Unit}}
 NavHost(nav,Routes.Splash){
  composable(Routes.Splash){SplashScreen()};composable(Routes.Welcome){WelcomeScreen({nav.navigate(Routes.Login)},{nav.navigate(Routes.SignUp)})}
  composable(Routes.Login){LoginScreen(state,vm::login,{nav.navigate(Routes.Forgot)},{nav.navigate(Routes.SignUp)})};composable(Routes.SignUp){SignUpScreen(state,vm::register)};composable(Routes.Forgot){ForgotScreen()}
  composable(Routes.Home){MainFeatureScreen("Latest tenders",Routes.Home,{nav.navigate(it){launchSingleTop=true}})}
  composable(Routes.Search){MainFeatureScreen("Search",Routes.Search,{nav.navigate(it){launchSingleTop=true}})};composable(Routes.Saved){MainFeatureScreen("Saved tenders",Routes.Saved,{nav.navigate(it){launchSingleTop=true}})};composable(Routes.Notifications){MainFeatureScreen("Notifications",Routes.Notifications,{nav.navigate(it){launchSingleTop=true}})};composable(Routes.Profile){MainFeatureScreen("Profile",Routes.Profile,{nav.navigate(it){launchSingleTop=true}},{nav.navigate(Routes.Account)})};composable(Routes.Account){AccountScreen(vm::logout)}
 }
}
