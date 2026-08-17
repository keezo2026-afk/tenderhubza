package za.co.tenderhub.core.auth
import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
interface TokenStore { fun get():String?; fun set(token:String); fun clear() }
class SecureTokenStore(context:Context):TokenStore {
 private val prefs=EncryptedSharedPreferences.create(context,"secure_auth",MasterKey.Builder(context).setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build(),EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM)
 override fun get()=prefs.getString("access_token",null); override fun set(token:String){prefs.edit().putString("access_token",token).apply()}; override fun clear(){prefs.edit().clear().apply()}
}
