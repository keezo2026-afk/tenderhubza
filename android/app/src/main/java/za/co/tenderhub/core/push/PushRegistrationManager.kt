package za.co.tenderhub.core.push
import android.content.Context
import com.google.firebase.FirebaseApp
import com.google.firebase.FirebaseOptions
import com.google.firebase.messaging.FirebaseMessaging
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import za.co.tenderhub.BuildConfig
import za.co.tenderhub.data.repository.NotificationRepository
class PushRegistrationManager(private val context:Context){private val prefs=context.getSharedPreferences("push_registration",Context.MODE_PRIVATE)
 fun configured()=BuildConfig.FIREBASE_API_KEY.isNotBlank()&&BuildConfig.FIREBASE_APP_ID.isNotBlank()&&BuildConfig.FIREBASE_PROJECT_ID.isNotBlank()&&BuildConfig.FIREBASE_SENDER_ID.isNotBlank()
 private fun initialize():Boolean{if(!configured())return false;if(FirebaseApp.getApps(context).isEmpty()){FirebaseApp.initializeApp(context,FirebaseOptions.Builder().setApiKey(BuildConfig.FIREBASE_API_KEY).setApplicationId(BuildConfig.FIREBASE_APP_ID).setProjectId(BuildConfig.FIREBASE_PROJECT_ID).setGcmSenderId(BuildConfig.FIREBASE_SENDER_ID).build())};return true}
 fun register(repository:NotificationRepository){if(!initialize())return;FirebaseMessaging.getInstance().token.addOnSuccessListener{token->prefs.edit().putString("token",token).apply();CoroutineScope(Dispatchers.IO).launch{repository.register(token,BuildConfig.VERSION_NAME)}}}
 fun onTokenChanged(token:String){prefs.edit().putString("token",token).apply()}
 fun unregister(repository:NotificationRepository,onComplete:()->Unit={}){val token=prefs.getString("token",null);CoroutineScope(Dispatchers.Main).launch{if(token!=null)repository.unregister(token);prefs.edit().clear().apply();onComplete()}}
}
