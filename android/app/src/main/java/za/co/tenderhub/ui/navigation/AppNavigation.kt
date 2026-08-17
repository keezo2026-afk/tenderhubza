package za.co.tenderhub.ui.navigation
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavType
import androidx.navigation.compose.*
import androidx.navigation.navArgument
import za.co.tenderhub.data.repository.TenderRepository
import za.co.tenderhub.ui.screens.*
private fun <T:ViewModel> factory(create:()->T)=object:ViewModelProvider.Factory{override fun <V:ViewModel> create(modelClass:Class<V>):V{@Suppress("UNCHECKED_CAST") return create() as V}}
@Composable fun AppNavigation(vm:AuthViewModel,tenders:TenderRepository){val nav=rememberNavController();val state by vm.state.collectAsState();val navigateMain:(String)->Unit={nav.navigate(it){launchSingleTop=true}};LaunchedEffect(state){when(state){is AuthState.Authenticated->nav.navigate(Routes.Home){popUpTo(0)};AuthState.Anonymous->if(nav.currentDestination?.route !in setOf(Routes.Welcome,Routes.Login,Routes.SignUp,Routes.Forgot))nav.navigate(Routes.Welcome){popUpTo(0)};else->Unit}}
 NavHost(nav,Routes.Splash){
  composable(Routes.Splash){SplashScreen()};composable(Routes.Welcome){WelcomeScreen({nav.navigate(Routes.Login)},{nav.navigate(Routes.SignUp)})};composable(Routes.Login){LoginScreen(state,vm::login,{nav.navigate(Routes.Forgot)},{nav.navigate(Routes.SignUp)})};composable(Routes.SignUp){SignUpScreen(state,vm::register)};composable(Routes.Forgot){ForgotScreen()}
  composable(Routes.Home){val home:HomeViewModel=viewModel(factory=factory{HomeViewModel(tenders)});val data by home.state.collectAsState();MainShell(Routes.Home,navigateMain){padding->androidx.compose.foundation.layout.Box(Modifier.padding(padding)){HomeDataScreen(data,home::load){nav.navigate(Routes.detail(it))}}}}
  composable(Routes.Search){val search:SearchViewModel=viewModel(factory=factory{SearchViewModel(tenders)});val data by search.state.collectAsState();MainShell(Routes.Search,navigateMain){padding->androidx.compose.foundation.layout.Box(Modifier.padding(padding)){SearchDataScreen(data,search::search,{search.search()},search::loadMore){nav.navigate(Routes.detail(it))}}}}
  composable(Routes.Saved){MainFeatureScreen("Saved tenders",Routes.Saved,navigateMain)};composable(Routes.Notifications){MainFeatureScreen("Notifications",Routes.Notifications,navigateMain)};composable(Routes.Profile){MainFeatureScreen("Profile",Routes.Profile,navigateMain){nav.navigate(Routes.Account)}};composable(Routes.Account){AccountScreen(vm::logout)}
  composable(Routes.Detail,arguments=listOf(navArgument("id"){type=NavType.StringType})){entry->val id=entry.arguments?.getString("id")!!;val detail:DetailViewModel=viewModel(key=id,factory=factory{DetailViewModel(id,tenders)});val data by detail.state.collectAsState();TenderDetailScreen(data,detail::load)}
 }
}
