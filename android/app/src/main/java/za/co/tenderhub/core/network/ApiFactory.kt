package za.co.tenderhub.core.network
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import za.co.tenderhub.BuildConfig
import za.co.tenderhub.core.auth.TokenStore
import za.co.tenderhub.data.remote.TenderHubApi
object ApiFactory {
 fun create(tokens:TokenStore):TenderHubApi {
  val auth=Interceptor { chain-> val request=chain.request().newBuilder().apply { tokens.get()?.let { header("Authorization","Bearer $it") } }.build(); chain.proceed(request) }
  val client=OkHttpClient.Builder().addInterceptor(auth).addInterceptor(HttpLoggingInterceptor().apply { level=if(BuildConfig.DEBUG) HttpLoggingInterceptor.Level.BASIC else HttpLoggingInterceptor.Level.NONE }).build()
  return Retrofit.Builder().baseUrl(BuildConfig.API_BASE_URL).client(client).addConverterFactory(GsonConverterFactory.create()).build().create(TenderHubApi::class.java)
 }
}
