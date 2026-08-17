package za.co.tenderhub.core.network
import okhttp3.*
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import za.co.tenderhub.BuildConfig
import za.co.tenderhub.core.auth.TokenStore
import za.co.tenderhub.data.remote.*
import za.co.tenderhub.domain.model.RefreshRequest
object ApiFactory {
 fun create(tokens:TokenStore):TenderHubApi {
  val converter=GsonConverterFactory.create();val refreshApi=Retrofit.Builder().baseUrl(BuildConfig.API_BASE_URL).client(OkHttpClient()).addConverterFactory(converter).build().create(RefreshApi::class.java)
  val auth=Interceptor{chain->chain.proceed(chain.request().newBuilder().apply{tokens.access()?.let{header("Authorization","Bearer $it")}}.build())}
  val authenticator=Authenticator{_,response->
   if(responseCount(response)>1||response.request.header("Authorization")==null)return@Authenticator null
   val refresh=tokens.refresh()?:return@Authenticator null
   try{val refreshed=refreshApi.refresh(RefreshRequest(refresh)).execute();val body=refreshed.body();if(refreshed.isSuccessful&&body!=null){tokens.set(body.access_token,body.refresh_token);response.request.newBuilder().header("Authorization","Bearer ${body.access_token}").build()}else{tokens.clear();null}}catch(_:Exception){tokens.clear();null}
  }
  val logging=HttpLoggingInterceptor().apply{level=if(BuildConfig.DEBUG)HttpLoggingInterceptor.Level.BASIC else HttpLoggingInterceptor.Level.NONE}
  val client=OkHttpClient.Builder().addInterceptor(auth).authenticator(authenticator).addInterceptor(logging).build();return Retrofit.Builder().baseUrl(BuildConfig.API_BASE_URL).client(client).addConverterFactory(converter).build().create(TenderHubApi::class.java)
 }
 private fun responseCount(response:Response):Int{var result=1;var prior=response.priorResponse;while(prior!=null){result++;prior=prior.priorResponse};return result}
}
