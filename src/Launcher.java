package cloudinspect.macos;
import java.nio.channels.*;
import java.nio.file.*;
public final class Launcher {
  private static FileChannel channel;
  private static FileLock lock;
  public static void main(String[] args) throws Exception {
    channel=FileChannel.open(Paths.get(".macos-instance.lock"),StandardOpenOption.CREATE,StandardOpenOption.WRITE);
    lock=channel.tryLock();
    if(lock==null) { System.err.println("Mac 客户端已经运行，请勿重复打开。");System.exit(2); }
    if(Boolean.getBoolean("cloudinspect.smoke")) {
      Thread t=new Thread(() -> {
        try {Thread.sleep(15000);}catch(InterruptedException e){return;}
        javafx.application.Platform.runLater(() -> {
          try {
            java.util.Iterator<javafx.stage.Window> windows=javafx.stage.Window.impl_getWindows();
            int i=0;
            while(windows.hasNext()) {
              javafx.stage.Window w=windows.next();
              if(w.isShowing() && w.getScene()!=null) {
                javafx.scene.image.WritableImage img=w.getScene().snapshot(null);
                javax.imageio.ImageIO.write(javafx.embed.swing.SwingFXUtils.fromFXImage(img,null),"png",new java.io.File("../diagnostics/window-"+(i++)+".png"));
              }
            }
            System.out.println("MAC_SMOKE_VISIBLE_WINDOWS="+i);
            if(Boolean.getBoolean("cloudinspect.smoke.patch")) {
              nc.cloudinspect.ui.CloudInspect.cloudInspectController.patchManageJob();
              javafx.animation.PauseTransition pause = new javafx.animation.PauseTransition(javafx.util.Duration.seconds(5));
              pause.setOnFinished(event -> {
                try {
                  java.util.Iterator<javafx.stage.Window> it=javafx.stage.Window.impl_getWindows();int j=0;
                  while(it.hasNext()) {javafx.stage.Window w=it.next();if(w.isShowing() && w.getScene()!=null)
                    javax.imageio.ImageIO.write(javafx.embed.swing.SwingFXUtils.fromFXImage(w.getScene().snapshot(null),null),"png",new java.io.File("../diagnostics/patch-"+(j++)+".png"));}
                  System.out.println("MAC_PATCH_VISIBLE_WINDOWS="+j);
                }catch(Exception ex){ex.printStackTrace();}
              });pause.play();
            }
          }catch(Exception e){e.printStackTrace();}
        });
      }); t.setDaemon(true);t.start();
    }
    javafx.application.Application.launch(nc.cloudinspect.ui.CloudInspect.class,args);
  }
}
