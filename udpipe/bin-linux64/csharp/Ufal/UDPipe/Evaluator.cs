//------------------------------------------------------------------------------
// <auto-generated />
//
// This file was automatically generated by SWIG (http://www.swig.org).
// Version 3.0.8
//
// Do not make changes to this file unless you know what you are doing--modify
// the SWIG interface file instead.
//------------------------------------------------------------------------------

namespace Ufal.UDPipe {

public class Evaluator : global::System.IDisposable {
  private global::System.Runtime.InteropServices.HandleRef swigCPtr;
  protected bool swigCMemOwn;

  internal Evaluator(global::System.IntPtr cPtr, bool cMemoryOwn) {
    swigCMemOwn = cMemoryOwn;
    swigCPtr = new global::System.Runtime.InteropServices.HandleRef(this, cPtr);
  }

  internal static global::System.Runtime.InteropServices.HandleRef getCPtr(Evaluator obj) {
    return (obj == null) ? new global::System.Runtime.InteropServices.HandleRef(null, global::System.IntPtr.Zero) : obj.swigCPtr;
  }

  ~Evaluator() {
    Dispose();
  }

  public virtual void Dispose() {
    lock(this) {
      if (swigCPtr.Handle != global::System.IntPtr.Zero) {
        if (swigCMemOwn) {
          swigCMemOwn = false;
          udpipe_csharpPINVOKE.delete_Evaluator(swigCPtr);
        }
        swigCPtr = new global::System.Runtime.InteropServices.HandleRef(null, global::System.IntPtr.Zero);
      }
      global::System.GC.SuppressFinalize(this);
    }
  }

  public Evaluator(Model m, string tokenizer, string tagger, string parser) : this(udpipe_csharpPINVOKE.new_Evaluator(Model.getCPtr(m), tokenizer, tagger, parser), true) {
    if (udpipe_csharpPINVOKE.SWIGPendingException.Pending) throw udpipe_csharpPINVOKE.SWIGPendingException.Retrieve();
  }

  public void setModel(Model m) {
    udpipe_csharpPINVOKE.Evaluator_setModel(swigCPtr, Model.getCPtr(m));
  }

  public void setTokenizer(string tokenizer) {
    udpipe_csharpPINVOKE.Evaluator_setTokenizer(swigCPtr, tokenizer);
    if (udpipe_csharpPINVOKE.SWIGPendingException.Pending) throw udpipe_csharpPINVOKE.SWIGPendingException.Retrieve();
  }

  public void setTagger(string tagger) {
    udpipe_csharpPINVOKE.Evaluator_setTagger(swigCPtr, tagger);
    if (udpipe_csharpPINVOKE.SWIGPendingException.Pending) throw udpipe_csharpPINVOKE.SWIGPendingException.Retrieve();
  }

  public void setParser(string parser) {
    udpipe_csharpPINVOKE.Evaluator_setParser(swigCPtr, parser);
    if (udpipe_csharpPINVOKE.SWIGPendingException.Pending) throw udpipe_csharpPINVOKE.SWIGPendingException.Retrieve();
  }

  public string evaluate(string data, ProcessingError error) {
    string ret = udpipe_csharpPINVOKE.Evaluator_evaluate__SWIG_0(swigCPtr, data, ProcessingError.getCPtr(error));
    if (udpipe_csharpPINVOKE.SWIGPendingException.Pending) throw udpipe_csharpPINVOKE.SWIGPendingException.Retrieve();
    return ret;
  }

  public string evaluate(string data) {
    string ret = udpipe_csharpPINVOKE.Evaluator_evaluate__SWIG_1(swigCPtr, data);
    if (udpipe_csharpPINVOKE.SWIGPendingException.Pending) throw udpipe_csharpPINVOKE.SWIGPendingException.Retrieve();
    return ret;
  }

  public static string DEFAULT {
    get {
      string ret = udpipe_csharpPINVOKE.Evaluator_DEFAULT_get();
      return ret;
    } 
  }

  public static string NONE {
    get {
      string ret = udpipe_csharpPINVOKE.Evaluator_NONE_get();
      return ret;
    } 
  }

}

}