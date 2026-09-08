package cloudinspect.macos;
import java.io.File;
public final class MacSupport {
  public static void setTipTime(javafx.scene.control.Tooltip tip, int millis) {
    tip.setShowDelay(javafx.util.Duration.millis(300));
    tip.setShowDuration(javafx.util.Duration.millis(millis));
    tip.setHideDelay(javafx.util.Duration.millis(300));
  }
  public static void openFile(String path) {
    try {
      File file = new File(path);
      if (!file.exists()) throw new java.io.IOException("文件不存在：" + path);
      new ProcessBuilder("/usr/bin/open", file.getAbsolutePath()).start();
    } catch (Exception e) {
      nc.cloudinspect.ui.utils.AlertUtils.displayError("打开文件失败：" + e.getMessage());
    }
  }
  public static void clientUpdate() {
    nc.cloudinspect.ui.utils.AlertUtils.displayWarning("Mac 适配版暂不支持工具自身的一键升级。请保留当前目录，使用新版本重新适配。此限制不针对业务补丁安装。");
  }
}
