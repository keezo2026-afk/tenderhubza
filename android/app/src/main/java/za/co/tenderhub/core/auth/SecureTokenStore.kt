package za.co.tenderhub.core.auth
import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
interface TokenStore {fun access():String?;fun refresh():String?;fun set(access:String,refresh:String);fun clear();val invalidations:SharedFlow<Unit>}
class SecureTokenStore(context:Context):TokenStore {
 private val prefs=EncryptedSharedPreferences.create(context,"secure_auth",MasterKey.Builder(context).setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build(),EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM)
 private val _invalidations=MutableSharedFlow<Unit>(extraBufferCapacity=1);override val invalidations:SharedFlow<Unit> =_invalidations
 override fun access()=prefs.getString("access_token",null);override fun refresh()=prefs.getString("refresh_token",null)
 @Synchronized override fun set(access:String,refresh:String){prefs.edit().putString("access_token",access).putString("refresh_token",refresh).apply()}
 @Synchronized override fun clear(){prefs.edit().clear().apply();_invalidations.tryEmit(Unit)}
}
